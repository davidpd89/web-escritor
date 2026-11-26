#!/usr/bin/env python3
"""Single writer for free, bounded publisher intake and generated-only PRs."""
import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import traceback
import urllib.request
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))  # módulos hermanos también al cargarlo con importlib
import git_estado
import gh_listas
import reading_cover_store as cover_store
import reading_quarantine
import catalogo_estado as estado
import presupuesto_sitio as presupuesto
import materializar_generados as materializar
from reading_intake_pipeline import ingest
from reading_intake_fetch import read_json, write_if_changed
from reading_ratings_refresh import refresh as refresh_ratings, google_response, hardcover_response, write_changed

ROOT = Path(__file__).resolve().parents[1]
TEXTS_PREFIX = 'automation/reading-catalogue-textos-'
# Datos consultados y aún sin PR: la siguiente ejecución los publica sin volver a consultar las fuentes.
CHECKPOINT_PREFIX = 'automation/reading-datos-'
spec = importlib.util.spec_from_file_location('reading_publication', ROOT / 'scripts/publish-reading-refresh.py')
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


# Lo que la ingesta consulta fuera (fichas, pendientes, valoraciones, precios, portadas, audio). Todo lo demás
# (fichas HTML, pagefind, mapas, registro) se reconstruye con el código actual y nunca se arrastra.
SOURCE_PATHS = ('data/reading-catalogue.json', 'assets/reading-market.json', 'data/reading-authors.json',
                'data/reading-publishers.json', 'data/reading-intake-state.json', 'data/reading-quarantine.json', 'data/reading-covers-store.json', 'assets/reading-covers', 'assets/reading-audio')


def command(*args):
    subprocess.run(args, cwd=ROOT, check=True)


PUSH_TIMEOUT = 900   # un push de ~2.000 ficheros tarda minutos; más de 15 es un push parado, no uno lento
PUSH_ATTEMPTS = 3


def push(*refspec, root=ROOT, timeout=PUSH_TIMEOUT, attempts=PUSH_ATTEMPTS):
    """`git push` que nunca se queda colgado: 22/11 la carga 44966182798 estuvo ~1 h en un push sin límite y hubo que
    cancelarla a mano. Corta la conexión si no avanza (LOW_SPEED), mata todo el grupo de procesos al agotar el tiempo
    y repite: un push repetido de la misma referencia es idempotente, así que un intento que sí llegó no hace daño."""
    env = {**os.environ, 'GIT_TERMINAL_PROMPT': '0', 'GIT_HTTP_LOW_SPEED_LIMIT': '1000', 'GIT_HTTP_LOW_SPEED_TIME': '120'}
    last = None
    for attempt in range(1, attempts + 1):
        proc = subprocess.Popen(['git', 'push', '--quiet', 'origin', *refspec], cwd=root, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=(os.name != 'nt'))
        try:
            out, err = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            if os.name != 'nt':
                os.killpg(proc.pid, 9)
            else:
                proc.kill()
            try:
                proc.communicate(timeout=10)  # un hijo huérfano podría retener las tuberías
            except subprocess.TimeoutExpired:
                pass
            last = f'sin terminar tras {timeout}s'
        else:
            if proc.returncode == 0:
                return
            last = (err or out).decode(errors='replace').strip()[-300:]
        print(f'::warning::git push {refspec[0][:60]} intento {attempt}/{attempts} falló: {last}', flush=True)
        if attempt < attempts:
            time.sleep(15 * attempt)
    raise RuntimeError(f'git push {refspec[0][:60]} falló tras {attempts} intentos: {last}')


RED = ('fetch', 'ls-remote')   # órdenes que hablan con GitHub; el push tiene su propio bucle (push())
RED_INTENTOS = 4


def git(*args, root=ROOT, data=None):
    """git con el resultado en bytes. fetch y ls-remote se repiten con espera ante un error (502, corte de red).

    follow_main() hace un fetch justo antes de save_checkpoint, tras ~80 min de ingesta: un 502 suelto ahí tiraba
    todo lo consultado sin guardarlo (S01 de la revisión GPT, 25/11). Las órdenes locales no se repiten."""
    intentos = RED_INTENTOS if args and args[0] in RED else 1
    for intento in range(1, intentos + 1):
        try:
            return subprocess.run(['git', *args], cwd=root, check=True, capture_output=True, input=data).stdout
        except subprocess.CalledProcessError as exc:
            if intento == intentos:
                raise
            causa = (exc.stderr or b'').decode(errors='replace').strip()[-200:]
            print(f'::warning::git {args[0]} falló (intento {intento}/{intentos}): {causa}', flush=True)
            time.sleep(10 * intento)


def replay(patch, onto, root=ROOT):
    """Checkout limpio en `onto` con `patch` aplicado a tres vías. Si choca, deja `onto` limpio y devuelve False."""
    git('reset', '--quiet', '--hard', root=root)
    git('clean', '--quiet', '-fd', root=root)
    git('switch', '--quiet', '--detach', onto, root=root)
    if not patch:
        return True
    if subprocess.run(['git', 'apply', '--3way', '--binary', '--whitespace=nowarn', '-'], cwd=root, input=patch,
                      capture_output=True).returncode == 0:
        return True
    git('reset', '--quiet', '--hard', root=root)
    git('clean', '--quiet', '-fd', root=root)
    return False


def catalogue_ids(raw):
    return {book['id'] for book in json.loads(raw)['libros']}


def follow_main(root=ROOT):
    """Lleva lo recién consultado al main más reciente antes de abrir la PR.

    La ingesta tarda ~25 min; lo que otro escritor fusiona en ese rato ya no deja la PR en conflicto al nacer.
    Si main cambió los mismos datos, la PR sale de la base de la ingesta y la CI de main decide.
    """
    git('fetch', '--quiet', 'origin', 'main', root=root)
    head, latest = (git('rev-parse', ref, root=root).decode().strip() for ref in ('HEAD', 'origin/main'))
    if head == latest:
        return head
    git('add', '--all', root=root)
    patch = git('diff', '--cached', '--binary', 'HEAD', root=root)
    if replay(patch, latest, root):
        print(f'Ingesta trasladada al main actual {latest[:12]}', flush=True)
        return latest
    if not replay(patch, head, root):
        raise RuntimeError('No se pudo restaurar la ingesta sobre su base')
    print('main cambió los mismos datos fuente: la PR sale de la base de la ingesta', flush=True)
    return head


def carry(branch, root=ROOT, skipped=None):
    """Datos fuente de una PR verde pero obsoleta, sobre el main actual y sin volver a consultar las fuentes.

    Devuelve las altas recuperadas frente a main, o None si ya están publicadas. Si los JSON chocan,
    conserva las altas con su procedencia sin rebobinar main. Los datos fuente viajan sin HTML viejo.
    """
    git('fetch', '--quiet', 'origin', 'main', f'+refs/heads/{branch}:refs/remotes/origin/{branch}', root=root)
    head, latest = (git('rev-parse', ref, root=root).decode().strip() for ref in ('origin/' + branch, 'origin/main'))
    base = git('merge-base', latest, head, root=root).decode().strip()
    patch = git('diff', '--binary', base, head, '--', *SOURCE_PATHS, root=root)
    before = catalogue_ids(git('show', latest + ':data/reading-catalogue.json', root=root))
    if not patch:
        return None
    if not replay(patch, latest, root):
        from reading_source_recovery import recover
        return recover(root, head, base, latest, skipped)
    added = sorted(catalogue_ids((root / 'data/reading-catalogue.json').read_bytes()) - before)
    # Un punto de guardado ya publicado no provoca otra publicación vacía ni rebobina la siguiente noche.
    if not added and not git('diff', 'HEAD', '--', *SOURCE_PATHS, root=root).strip():
        return None
    return added


def bot_identity(root=ROOT):
    git('config', 'user.name', 'github-actions[bot]', root=root)
    git('config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com', root=root)


def save_checkpoint(day, root=ROOT):
    """Sube a una rama propia los datos fuente recién consultados, antes de construir páginas y de las pruebas.

    Si algo falla después (una prueba, un generador, el límite de tiempo del job), la siguiente ejecución los
    publica con `carry` sin repetir la ingesta. Usa un índice temporal: ni HEAD ni el índice real cambian.
    """
    # El punto de guardado registra portadas del almacén externo: sus bytes se suben antes, o una ejecución
    # posterior podría publicar el catálogo con portadas que no existen (Codex #1495). Sin almacén: no-op.
    cover_store.flush('Portadas de la carga ' + day, root)
    paths = [p for p in SOURCE_PATHS if (root / p).exists()]
    index = root / git('rev-parse', '--git-path', 'checkpoint-index', root=root).decode().strip()
    env = {**os.environ, 'GIT_INDEX_FILE': str(index)}
    try:
        subprocess.run(['git', 'read-tree', 'HEAD'], cwd=root, check=True, capture_output=True, env=env)
        git_estado.preparar(root, paths, env=env)
        tree = subprocess.run(['git', 'write-tree'], cwd=root, check=True, capture_output=True, text=True, env=env).stdout.strip()
    finally:
        index.unlink(missing_ok=True)
    if tree == git('rev-parse', 'HEAD^{tree}', root=root).decode().strip():
        return None
    bot_identity(root)
    commit = git('commit-tree', tree, '-p', 'HEAD', '-m', 'Datos consultados de la carga ' + day, root=root).decode().strip()
    branch = publisher.publication.fresh_branch(CHECKPOINT_PREFIX + day + '-', cwd=root)
    push(f'{commit}:refs/heads/{branch}', root=root)
    print('Datos guardados en ' + branch, flush=True)
    return branch


def checkpoints(root=ROOT):
    out = git('ls-remote', '--heads', 'origin', CHECKPOINT_PREFIX + '*', root=root).decode()
    return sorted(line.split('refs/heads/', 1)[1] for line in out.splitlines() if 'refs/heads/' in line)


def drop_checkpoint(branch, root=ROOT):
    if branch:
        subprocess.run(['git', 'push', '--quiet', 'origin', '--delete', branch], cwd=root, check=False)


def radar_isbns(config):
    """Novedades y próximos lanzamientos de Amazon que faltan en el catálogo, más nuevos primero.

    De Amazon solo se usa el ISBN, en esta misma ejecución (su licencia no permite guardar más);
    la ficha la lee la ingesta en todostuslibros. El informe va a la CI solo con cifras agregadas.
    """
    amazon_id = os.getenv('AMAZON_CREATORS_CLIENT_ID', '').strip()
    amazon_secret = os.getenv('AMAZON_CREATORS_CLIENT_SECRET', '').strip()
    if not (config.get('amazon_radar', {}).get('enabled') and amazon_id and amazon_secret):
        return []
    from reading_amazon_market import CreatorsPrices
    from reading_amazon_radar import run as amazon_radar
    isbns, tag = [], config['amazon_partner_tag']
    try:
        radar = amazon_radar(CreatorsPrices(amazon_id, amazon_secret, tag), read_json(ROOT / 'data/reading-catalogue.json'),
                             config.get('publisher_aliases', []), tag, pages=int(config['amazon_radar'].get('pages', 10)), collect=isbns,
                             max_requests=int(config['amazon_radar'].get('max_requests', 10)),
                             max_depth=int(config['amazon_radar'].get('max_depth', 0)))
    except (RuntimeError, ValueError, OSError) as exc:  # sin radar, la ingesta sigue con las editoriales
        radar = {'error': str(exc)[:300]}
    write_if_changed(ROOT / '.ci/reading-intake/amazon-radar.json', {**radar, 'isbn_a_ingesta': len(isbns)})
    print('Radar Amazon: ' + json.dumps({**radar, 'isbn_a_ingesta': len(isbns)}, ensure_ascii=True), flush=True)
    return isbns


# Rama de una carga del propio escritor: 'automation/reading-catalogue-' + día + '-' (ver fresh_branch más abajo).
OWN_BATCH = re.compile(r'automation/reading-catalogue-\d{4}-\d{2}-\d{2}-[A-Za-z0-9-]+')


def pending_batches(opened):
    """Cargas del propio escritor, reconocidas por su forma de rama y no por exclusión.

    Otros bucles comparten el prefijo (textos, auditoría de Amazon) y gestionan sus propias PR. Excluirlos uno a uno
    dejó pasar la auditoría de Amazon: la PR #1268, firmada con la identidad local, se tomó como carga pendiente y
    resume_pending abortó las cuatro ejecuciones de la noche del 11/11 sin cargar nada.
    """
    return [p['headRefName'] for p in opened if OWN_BATCH.fullmatch(p['headRefName'])]


def reconcile_pending(pending, root=ROOT):
    """Varias cargas abiertas no paran la noche (Fable F8): se queda la más nueva y las demás pasan a puntos de guardado.

    Antes, dos PR abiertas abortaban cada ejecución con «Hay varias cargas pendientes» hasta que alguien cerraba una.
    Crear antes de destruir: la cabeza de cada PR vieja se copia a una rama `reading-datos-*` y solo después se cierra
    la PR (su rama se conserva). Las ejecuciones siguientes la publican con `carry`, sin volver a consultar las fuentes.
    """
    if len(pending) == 1:
        return pending[0]
    gh = publisher.publication.gh
    numbered = sorted((json.loads(gh('pr', 'view', branch, '--json', 'number'))['number'], branch) for branch in pending)
    *older, (_, newest) = numbered
    for number, branch in older:
        git('fetch', '--quiet', 'origin', f'+refs/heads/{branch}:refs/remotes/origin/{branch}', root=root)
        day = re.search(r'\d{4}-\d{2}-\d{2}', branch).group(0)
        saved = publisher.publication.fresh_branch(CHECKPOINT_PREFIX + day + '-', cwd=root)
        push(f'refs/remotes/origin/{branch}:refs/heads/{saved}', root=root)
        publisher.close_proposal(number, f'Había varias cargas abiertas: se queda la más nueva. Sus datos pasan a `{saved}` '
                                 f'y se publican sin nueva consulta en las siguientes ejecuciones. Se conserva la rama `{branch}`.')
    return newest


STUCK_PREFIX = 'automation/reading-atascado-'


def reconcile_deploy(root=ROOT):
    """Una muerte entre fusionar y desplegar no deja main sin publicar (Fable R4-6, F3).

    Una fusión con GITHUB_TOKEN no dispara el despliegue por push: lo lanza el publicador justo después. Si la
    ejecución muere entre los dos pasos, nadie despliega. Al empezar, si la punta de main no tiene un despliegue
    en curso ni terminado en verde, se lanza uno. Devuelve True si lo lanzó.
    """
    gh = publisher.publication.gh
    git('fetch', '--quiet', 'origin', 'main', root=root)
    sha = git('rev-parse', 'origin/main', root=root).decode().strip()
    repo = gh('repo', 'view', '--json', 'nameWithOwner', '--jq', '.nameWithOwner').strip()
    runs = json.loads(gh('api', f'repos/{repo}/actions/workflows/deploy-pages.yml/runs?head_sha={sha}'))['workflow_runs']
    if any(r.get('status') != 'completed' for r in runs):
        return False

    def deployed(run):
        # Un run en verde puede no haber desplegado: el disparo horario descartado (`seguir=false`) salta `deploy`.
        jobs = json.loads(gh('api', f'repos/{repo}/actions/runs/{run["id"]}/jobs'))['jobs']
        return any(j.get('name') == 'deploy' and j.get('conclusion') == 'success' for j in jobs)
    if any(r.get('conclusion') == 'success' and deployed(r) for r in runs):
        return False
    print(f'::warning::main {sha[:12]} sin despliegue en verde ni en curso; se despliega ahora', flush=True)
    gh('workflow', 'run', 'deploy-pages.yml', '--ref', 'main')
    return True


def keep_copy(source, root=ROOT):
    """Copia un punto de guardado a `reading-atascado-*`. Devuelve la copia, o None si no se pudo crear."""
    keep = STUCK_PREFIX + source[len(CHECKPOINT_PREFIX):]
    try:
        # La referencia remota puede no existir en este checkout si `carry` falló antes de descargarla.
        git('fetch', '--quiet', 'origin', f'+refs/heads/{source}:refs/remotes/origin/{source}', root=root)
        push(f'refs/remotes/origin/{source}:refs/heads/{keep}', root=root)
    except Exception as exc:  # noqa: BLE001
        print(f'::error::No se pudo copiar {source} a {keep} ({exc}); se conserva el original', flush=True)
        return None
    return keep


def open_stuck_issue(keep, body):
    try:
        publisher.publication.gh('issue', 'create', '--title', f'Carga: datos sin trasladar en {keep}', '--body', body)
    except Exception as issue_exc:  # noqa: BLE001
        print(f'::error::No se pudo abrir la issue ({issue_exc}); los datos siguen en {keep}', flush=True)


def report_skipped(source, skipped, root=ROOT):
    """Altas apartadas por falta de procedencia: el resto se publica; ellas quedan en una copia con su issue."""
    if not skipped:
        return None
    keep = keep_copy(source, root) if source.startswith(CHECKPOINT_PREFIX) else source
    print(f'::warning::{len(skipped)} altas sin procedencia apartadas de {source}: {", ".join(skipped[:20])}', flush=True)
    if keep:
        open_stuck_issue(keep, f'Altas sin procedencia publicada, apartadas al trasladar `{source}`: '
                         f'{", ".join(skipped[:100])}.\n\nEl resto del lote se publicó. Sus datos siguen en `{keep}`.')
    return keep


def report_stuck(source, exc, *, number=None, root=ROOT):
    """Unos datos que no se pueden trasladar no paran la noche ni se pierden (Fable R4-6, F3).

    Antes, un `carry` que lanzaba (procedencia ausente, blob que falta) tumbaba cada ejecución en el mismo punto
    de guardado o en la misma PR. Crear antes de destruir: un punto de guardado pasa a `reading-atascado-*` antes
    de borrarse; una PR se cierra conservando su rama. En los dos casos queda una issue con la causa.
    """
    git('reset', '--quiet', '--hard', root=root)
    git('clean', '--quiet', '-fd', root=root)
    keep = keep_copy(source, root) if source.startswith(CHECKPOINT_PREFIX) else source
    cause = f'{type(exc).__name__}: {exc}'[:1500]
    if keep is None:
        # Sin copia no se destruye nada: el punto de guardado sigue y la noche continúa con una consulta nueva.
        print(f'::error::{source} no se puede trasladar ({cause}); se conserva el original', flush=True)
        return source
    print(f'::error::{source} no se puede trasladar ({cause}); se conserva en {keep}', flush=True)
    open_stuck_issue(keep, f'`carry` falló con `{cause}`.\n\nLos datos siguen en la rama `{keep}`. La noche siguió '
                     'con una consulta nueva; nada se ha descartado. Hay que revisar la causa y trasladarlos a mano o '
                     'arreglar la recuperación.')
    if number is not None:
        publisher.close_proposal(number, f'Sus datos no se pueden trasladar al main actual ({cause[:300]}). Se conserva la '
                                 'rama y queda una issue; el escritor vuelve a consultar las fuentes.')
    else:
        drop_checkpoint(source, root=root)
    return keep


def chain_report(accepted, consumed=None, **extra):
    """Lo que lee la cadena nocturna (reading-catalogue-sync.yml): sigue si hubo altas o quedan puntos de guardado.

    Una carga recuperada o reanudada también encadena mientras queden datos guardados: con varios checkpoints, una
    noche sin altas nuevas los vaciaba de uno en uno solo con el cron (F8)."""
    # Un lote recuperado o trasladado no consultó las fuentes: la noche aún debe su consulta, aunque el lote no
    # trajera altas (21/11, carga 44843220015: un punto de guardado ya publicado gastó el turno y entraron 0 libros).
    # Una carga reanudada tampoco consultó: `resume_pending` → `run` solo vuelve tras fusionar (si no, lanza), así que
    # su PR ya no está abierta y la siguiente carga consulta (25/11, caso 8 de la revisión GPT: antes la cadena
    # paraba ahí y la noche se quedaba sin consulta).
    pending = int(bool(extra.get('recuperado_de') or extra.get('trasladada_de') or extra.get('reanudada')))
    write_if_changed(ROOT / '.ci/reading-intake/publisher-report.json',
                     {**extra, 'stats': {'accepted': accepted, 'checkpoints_restantes': len(set(checkpoints()) - {consumed}),
                                         'consulta_pendiente': pending}})


def refresh(*, publish=False):
    config = read_json(ROOT / 'data/reading-intake-config.json')
    if publish and subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=all'], cwd=ROOT, text=True).strip():
        raise ValueError('La publicación automática exige un checkout limpio')
    if publish and not config.get('autopublish'):
        raise ValueError('Autopublicación desactivada en la configuración')
    if publish:
        reconcile_deploy()
    # A failed previous batch stays inspectable; never pile up duplicate writers.
    opened = gh_listas.lista(publisher.publication.gh, 'pr', 'list', '--state', 'open', '--base', 'main', '--json', 'headRefName')
    pending = pending_batches(opened)
    if pending:
        current = reconcile_pending(pending) if publish else pending[-1]
        action = publisher.resume_pending(current) if publish else 'resumed'
        if action == 'resumed':
            print('Carga pendiente conservada: ' + current)
            if publish:
                chain_report(0, reanudada=current)
            return
        if action == 'carry':
            replaced = json.loads(publisher.publication.gh('pr', 'view', current, '--json', 'number'))['number']
            skipped = []
            try:
                carried = carry(current, skipped=skipped)
            except Exception as exc:  # noqa: BLE001
                report_stuck(current, exc, number=replaced)
                carried = replaced = None
            report_skipped(current, skipped)
            if carried is not None:
                print(f'Datos de #{replaced} trasladados a main sin nueva consulta: {len(carried)} libros nuevos', flush=True)
                chain_report(len(carried), trasladada_de=current, new_books=carried)
                return assemble({'new_books': carried, 'updated_books': [], 'stats': {}}, changed=True,
                                replaced=replaced, source=current)
            if replaced is not None:
                publisher.close_proposal(replaced, 'Sus datos fuente ya están en main (o main ganó en los mismos libros). Se conserva '
                                         'esta propuesta y su rama como referencia; el escritor vuelve a consultar las fuentes.')
    if publish:
        # Una ejecución anterior consultó y no llegó a abrir PR: se publica eso, sin consultar de nuevo.
        for saved in checkpoints():
            skipped = []
            try:
                carried = carry(saved, skipped=skipped)
            except Exception as exc:  # noqa: BLE001
                report_stuck(saved, exc)
                continue
            if skipped and report_skipped(saved, skipped) is None:
                # Sin copia de las apartadas no se publica (eso borraría el punto de guardado): se reintenta mañana.
                git('reset', '--quiet', '--hard')
                git('clean', '--quiet', '-fd')
                continue
            if carried is None:
                print(f'{saved}: ya está en main; se descarta', flush=True)
                drop_checkpoint(saved)
                continue
            print(f'Datos de {saved} recuperados sin nueva consulta: {len(carried)} libros nuevos', flush=True)
            # La cadena nocturna lee el informe: un lote recuperado también encadena el siguiente.
            chain_report(len(carried), consumed=saved, recuperado_de=saved, new_books=carried)
            return assemble({'new_books': carried, 'updated_books': [], 'stats': {}}, changed=True, checkpoint=saved)
    amazon = config.get('amazon_catalogo', {}).get('enabled')
    failure = None
    if amazon and publish:
        # Un fallo de las altas no puede dejar la noche sin precios ni portadas (09/11: un ISBN repetido tumbó
        # refresh() antes de market_refresh). Se deshacen sus escrituras, siguen precios y portadas y la noche acaba
        # degradada (issue por causa), no en rojo: un rojo cortaba la cadena y lanzaba un reintento inútil (R2-07).
        # SystemExit también: catalogo_amazon sale así sin credenciales o con una respuesta ilegible (R2-04 GPT, 26/11).
        try:
            report = amazon_intake(config, publish)
        except (Exception, SystemExit) as exc:  # noqa: BLE001
            failure = exc
            print(f'::error::Altas de Amazon fallidas ({type(exc).__name__}: {exc}); se descartan y siguen precios y portadas',
                  flush=True)
            discard_intake_writes()
            report = {'new_books': [], 'updated_books': [], 'stats': {'accepted': 0, 'fuente': 'amazon_catalogo',
                                                                      'error': f'{type(exc).__name__}: {exc}'}}
    elif amazon:
        report = amazon_intake(config, publish)
    else:
        report = ingest(config, ROOT, ROOT / '.ci/reading-editorial-cache', apply=publish, isbns=radar_isbns(config))
    write_if_changed(ROOT / '.ci/reading-intake/publisher-report.json', report)
    print(json.dumps(report['stats'], ensure_ascii=True), flush=True)
    if not publish:
        return
    # Un fallo de precios o portadas (API caída, respuesta rara de un libro) no puede llevarse las altas: antes
    # tumbaba la carga antes de save_checkpoint y la noche se perdía. Se deshace solo lo escrito por el mercado.
    antes = git_estado.foto(ROOT, *SOURCE_PATHS)
    market_failure = None
    MARKET_STATUS.clear()
    try:
        changed = market_refresh(config)
    except (Exception, SystemExit) as exc:  # noqa: BLE001
        market_failure = exc
        print(f'::error::Precios y portadas fallidos ({type(exc).__name__}: {exc}); se deshacen y siguen las altas',
              flush=True)
        git_estado.restaurar(ROOT, antes, *SOURCE_PATHS)
        changed = False
    if market_failure is None and MARKET_STATUS.get('precios') in PROVIDER_DOWN:
        # refresh_offers no lanza si el proveedor cae: devuelve el estado. Cuenta como fase fallida (los grupos ya
        # guardados se quedan, no se deshacen), para que ningún aviso diga que se publicaron los precios (CodeRabbit #1595).
        market_failure = RuntimeError(f"proveedor de precios: {MARKET_STATUS['precios']}")
    follow_main()
    day = datetime.now(ZoneInfo('Europe/Madrid')).date().isoformat()
    saved = save_checkpoint(day)
    health_report(config)
    if amazon and not failure:
        # Solo ahora: los libros ya están a salvo en la rama de datos (o no había nada), así que la cola de
        # semillas puede avanzar sin perder ninguno si después falla la PR.
        estado.guardar(f'Estado de la ingesta {day}: {len(report["new_books"])} altas')
    result = assemble(report, changed=changed, checkpoint=saved)
    # R3-12 GPT (26/11): si fallan las dos, ninguna frase puede decir que la otra sí se publicó.
    both = failure is not None and market_failure is not None
    degrade('altas de Amazon', failure, 'tampoco se renovaron precios' if both else 'precios y portadas sí se publicaron')
    degrade('precios y portadas', market_failure, 'tampoco hubo altas' if both else 'las altas sí se publicaron')
    if both:
        raise failure  # nada se publicó: en rojo para que entre el reintento (puede ser la red o el proveedor)
    return result


def degrade(phase, exc, kept):
    """Una fase que falló sin llevarse la otra: issue `fallo` por causa (una, no una por noche) y aviso en el job.

    La carga sale en verde para que la cadena siga y el reintento no repita lo ya publicado."""
    if exc is None:
        return
    cause = f'{type(exc).__name__}: {exc}'[:300]
    text = f'Carga degradada: fallaron las {phase} ({cause}); {kept}.'
    print(f'::error::{text}', flush=True)
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as fh:
            fh.write(text + '\n')
    run = publisher.publication.run_url()
    trace = ''.join(traceback.format_exception(exc))[-3000:]
    try:
        open_issue(f'Carga degradada: {phase} ({type(exc).__name__})',
                   f'{text}\n\nRun: {run}\n\n```\n{trace}\n```')
    except Exception as issue_exc:  # noqa: BLE001 - R3-09 GPT (26/11): sin issue, el aviso queda en el log y el resumen
        print(f'::warning::No se pudo abrir la issue de carga degradada: {type(issue_exc).__name__}: {issue_exc}', flush=True)


INTAKE_PATHS = ('data', 'assets/reading-covers')


def discard_intake_writes(root=ROOT):
    """Deshace lo que una ingesta a medias dejó en el catálogo y las portadas (seguidos y nuevos)."""
    tracked = [p for p in INTAKE_PATHS if subprocess.run(['git', 'ls-files', '--', p], cwd=root, check=True,
                                                         capture_output=True, text=True).stdout.strip()]
    if tracked:
        subprocess.run(['git', 'checkout', 'HEAD', '--', *tracked], cwd=root, check=True)
    subprocess.run(['git', 'clean', '-fdq', '--', *INTAKE_PATHS], cwd=root, check=True)


def health_report(config):
    """Salud del catálogo (scripts/catalogue-health-report.py): solo informa y nunca para la carga.

    Va antes de estado.guardar para que su copia (.local/catalogo/salud.json) viaje en la rama catalogo-estado y la
    noche siguiente compare con esta."""
    budget = str(int(config.get('salud_catalogo', {}).get('consultas_amazon', 20)))
    try:
        subprocess.run([sys.executable, 'scripts/catalogue-health-report.py', '--amazon', budget], cwd=ROOT,
                       check=False, timeout=900)
    except Exception as exc:  # noqa: BLE001 - un informe roto no puede tumbar la publicación
        print(f'Informe de salud no generado: {exc}', flush=True)


def amazon_intake(config, publish):
    """Altas de scripts/catalogo_amazon.py (semillas por ISBN + sellos) con el estado de la rama catalogo-estado.

    Mismo informe que la ingesta editorial: `new_books` y `stats.accepted` encadenan el siguiente lote nocturno.
    En prueba (sin --publish) no se toca el catálogo ni se guarda el estado."""
    settings = config['amazon_catalogo']
    estado.restaurar()
    catalogue_path = ROOT / 'data/reading-catalogue.json'
    before = catalogue_ids(catalogue_path.read_bytes())
    day = datetime.now(ZoneInfo('Europe/Madrid')).date().isoformat()
    altas = int(settings.get('altas', 1000))
    if publish:
        # R5-1: Pages admite 1 GB. Sin sitio (o sin medida) no hay altas; precios y fechas siguen. No es un fallo:
        # la noche acaba degradada y no despierta al reparador. `--altas 0` no sirve: catalogo_amazon lo toma por 1000.
        libros_ahora = presupuesto.publicados(json.loads(catalogue_path.read_bytes()))
        altas = min(altas, presupuesto.cupo_de_hoy(estado.WORK, day, libros_ahora))
        if altas <= 0:
            print('::warning::Sin presupuesto de sitio para altas esta noche (clase presupuesto); siguen precios y fechas',
                  flush=True)
            return {'new_books': [], 'updated_books': [], 'stats': {'accepted': 0, 'fuente': 'amazon_catalogo',
                                                                   'degradada': 'presupuesto'}}
    # La prueba solo comprueba credenciales y fuentes con unas pocas peticiones: ni transforma ni gasta cuota.
    phase, requests = ('todo', int(settings.get('peticiones', 600))) if publish else ('descargar', 20)
    import catalogo_amazon
    code = catalogo_amazon.main([phase, '--dia', day, '--peticiones', str(requests), '--altas', str(altas)])
    new = sorted(catalogue_ids(catalogue_path.read_bytes()) - before)
    if publish:
        presupuesto.anotar(estado.WORK, day, len(new))
    summary = read_json(catalogo_amazon.WORK / f'informe-{day}.json', {})
    if code:
        # Libros vaciados o desaparecidos respecto a la foto anterior. No lo causa la ingesta (solo añade y enlaza);
        # abortar dejaría la foto vieja en catalogo-estado y bloquearía todas las noches siguientes. Se avisa.
        print('::warning::Revisión del catálogo: campos vaciados o libros desaparecidos respecto a la foto anterior; '
              'ver .ci/reading-intake/amazon-catalogo.json', flush=True)
    write_if_changed(ROOT / '.ci/reading-intake/amazon-catalogo.json', summary)
    return {'new_books': new, 'updated_books': [], 'stats': {'accepted': len(new), 'fuente': 'amazon_catalogo',
                                                               'regresion': bool(code)}}


PROVIDER_DOWN = ('provider_unavailable', 'pending_amazon_eligibility')
MARKET_STATUS = {}  # estado del barrido de precios de la última market_refresh (refresh_offers no lanza)


def market_refresh(config):
    """Valoraciones, formatos, portadas y precios: devuelve si cambió algún dato publicado."""
    MARKET_STATUS.clear()
    # This runs DAILY, even when publishers have no new ISBNs.
    # Single writer and ONE generated PR for publisher + rating changes.
    market_path = ROOT / 'assets/reading-market.json'
    market = read_json(market_path)
    ratings_config = config.get('ratings_refresh', {})
    ratings_stats = {}
    changed_ratings = False
    if ratings_config.get('enabled', False):
        books = read_json(ROOT / 'data/reading-catalogue.json')
        now = datetime.now(timezone.utc)
        google_key = os.getenv('GOOGLE_BOOKS_API_KEY', '').strip()
        hardcover_key = os.getenv('HARDCOVER_API_KEY', '').strip()
        providers = [
            ('google_books', google_key, google_response, int(ratings_config.get('google_books_requests_per_day', 25))),
            ('hardcover', hardcover_key, hardcover_response, int(ratings_config.get('hardcover_requests_per_day', 0))),
        ]
        from reading_goodreads import GoodreadsPublic
        goodreads = GoodreadsPublic()
        providers.insert(0, ('goodreads', 'public', lambda isbn, unused: goodreads(isbn), int(ratings_config.get('goodreads_requests_per_day', 40))))
        for source, secret, query, budget in providers:
            if not secret or not budget:
                ratings_stats[source] = {'status': 'sin_credencial_o_deshabilitado'}
                continue
            # A failing provider must not prevent the publisher intake or corrupt
            # existing ratings. Failures remain in the CI report.
            def provider(isbn, query=query, secret=secret):
                return query(isbn, secret)
            market, stats = refresh_ratings(books, market, provider, now=now,
                                            budget=budget, source=source)
            ratings_stats[source] = stats
        changed_ratings = write_changed(market_path, market)
    if ratings_stats:
        write_if_changed(ROOT / '.ci/reading-intake/ratings-report.json', ratings_stats)
        print('Valoraciones: ' + json.dumps(ratings_stats, ensure_ascii=True), flush=True)
    # Recheck existing free API access once each day. While Amazon refuses
    # eligibility the provider stops at its first error and prices stay absent.
    amazon_config=config.get('amazon_price_refresh',{})
    if amazon_config.get('page_formats_per_run',0):
        # Audible and many Kindle/hardcover editions never show up in Creators search: the format
        # selector of the book's own Amazon page lists them. The API sweep below prices them.
        from reading_amazon_market import discover_page_formats, fetch_amazon_page
        books=read_json(ROOT/'data/reading-catalogue.json')
        format_stats=discover_page_formats(books,fetch_amazon_page,config['amazon_partner_tag'],
                                           datetime.now(timezone.utc),limit=int(amazon_config['page_formats_per_run']))
        print('Formatos Amazon (ficha): '+json.dumps(format_stats,ensure_ascii=True),flush=True)
        changed_ratings=write_changed(ROOT/'data/reading-catalogue.json',books) or changed_ratings
    if amazon_config.get('real_covers_per_run'):
        from reading_amazon_market import discover_real_covers, fetch_amazon_image, fetch_amazon_page
        from reading_intake_pipeline import amazon_cover_bytes as cover_bytes
        books=read_json(ROOT/'data/reading-catalogue.json')
        cover_stats=discover_real_covers(books,ROOT,fetch_amazon_page,fetch_amazon_image,cover_bytes,
                                         datetime.now(timezone.utc),limit=int(amazon_config['real_covers_per_run']))
        print('Portadas Amazon: '+json.dumps(cover_stats,ensure_ascii=True),flush=True)
        changed_ratings=write_changed(ROOT/'data/reading-catalogue.json',books) or changed_ratings
    amazon_id=os.getenv('AMAZON_CREATORS_CLIENT_ID','').strip()
    amazon_secret=os.getenv('AMAZON_CREATORS_CLIENT_SECRET','').strip()
    if amazon_config.get('enabled') and amazon_id and amazon_secret:
        from reading_amazon_market import CreatorsPrices, fetch_amazon_image, refresh_offers, swap_cover
        from reading_intake_pipeline import amazon_cover_bytes as cover_bytes
        books=read_json(ROOT/'data/reading-catalogue.json')
        tag=config['amazon_partner_tag']
        now=datetime.now(timezone.utc)
        provider=CreatorsPrices(amazon_id,amazon_secret,tag)
        if amazon_config.get('cover_recheck_requests',600):
            # Portadas aparte del barrido de precios: cada noche se repasan todas las tipográficas.
            from reading_amazon_market import recheck_generated_covers
            cover_stats=recheck_generated_covers(books,ROOT,provider,fetch_amazon_image,cover_bytes,now,fetch_json=fetch_cover_json,
                                                 max_requests=int(amazon_config.get('cover_recheck_requests',600)))
            print('Portadas (repaso): '+json.dumps(cover_stats,ensure_ascii=True),flush=True)
        # Nightly sweep: prices are written into formatos_compra and the pages are
        # rebuilt below; prices stay published until a newer one replaces them. The same answer
        # brings the edition's cover: a book still on its typographic cover gets the real one.
        market,price_stats=refresh_offers(books,market,provider,tag,
                                         now,sweep_days=int(amazon_config.get('sweep_days',7)),
                                         cover=lambda book,url:swap_cover(book,ROOT,url,fetch_amazon_image,cover_bytes,now.date().isoformat()))
        MARKET_STATUS['precios']=price_stats.get('status')
        write_if_changed(ROOT/'.ci/reading-intake/prices-report.json',price_stats)
        print('Precios Amazon: '+json.dumps(price_stats,ensure_ascii=True),flush=True)
        changed_ratings=write_changed(ROOT/'data/reading-catalogue.json',books) or changed_ratings
        # Puestos de «más vendidos»: dato de mercado con caducidad, fuera de la ficha del libro.
        changed_ratings=write_changed(market_path,market) or changed_ratings
    return changed_ratings


def fetch_cover_json(url):
    """JSON de Google Books para buscar cubiertas por ISBN; con GOOGLE_BOOKS_API_KEY no comparte la cuota anónima."""
    key=os.getenv('GOOGLE_BOOKS_API_KEY','').strip()
    request=urllib.request.Request(url+(f'&key={key}' if key else ''),headers={'User-Agent':'web-escritor-portadas/1.0'})
    with urllib.request.urlopen(request,timeout=20) as response:
        return json.loads(response.read(2_000_000))


def quarantine_summary(quarantined, released):
    """Cuarentena agrupada por causa (la unidad de corrección) y libros que una regla corregida ha liberado."""
    groups = {}
    for h in quarantined:
        groups.setdefault(h.get('causa') or reading_quarantine.cause(h['motivo']), []).append(h['libro']['id'])
    lines = [f"- En cuarentena ({len(ids)}): {why} — " + ', '.join(f'`{i}`' for i in ids[:8]) + (' …' if len(ids) > 8 else '') + '\n'
             for why, ids in sorted(groups.items(), key=lambda kv: -len(kv[1]))]
    if released:
        lines.append('- Liberados de la cuarentena: ' + ', '.join(f'`{i}`' for i in sorted(released)) + '\n')
    return ''.join(lines) + ('\n' if lines else '')


def quarantine_alert_note():
    if not reading_quarantine.LAST['alert']:
        return ''
    return '**Alerta de cuarentena:** más del 5 % de las altas apartadas; se publica lo válido y queda una issue `fallo` por causa.\n\n'


def quarantine_alert(report, quarantined):
    """Muchas altas apartadas: se publica lo válido, pero la carga no se da por limpia y queda una issue por causa."""
    if not reading_quarantine.LAST['alert']:
        return
    report['quarantine_rate_alert'] = True
    # Se añade al informe guardado, no se sustituye: un lote recuperado guarda ahí stats.accepted y recuperado_de,
    # y la cadena nocturna lee stats.accepted. Un fallo al escribirlo no tumba la publicación de lo válido.
    path = ROOT / '.ci/reading-intake/publisher-report.json'
    try:
        saved = read_json(path) if path.exists() else {}
        write_if_changed(path, {**report, **saved, 'quarantine_rate_alert': True})
    except (OSError, ValueError) as exc:
        print(f'::warning::No se pudo marcar la alerta en publisher-report.json: {exc}', flush=True)
    groups = {}
    for h in quarantined:
        groups.setdefault(h.get('causa') or reading_quarantine.cause(h['motivo']), []).append(h['libro']['id'])
    print(f'::warning::Cuarentena alta: {len(quarantined)} libros apartados en {len(groups)} causas; se publica lo válido', flush=True)
    summary = os.getenv('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as fh:
            fh.write('**Carga con alerta de cuarentena** (no es una carga limpia):\n\n' + quarantine_summary(quarantined, set()))
    if not os.getenv('GITHUB_ACTIONS') or os.getenv('DRY_RUN') == 'true':  # el ensayo no abre issues reales
        return
    for why, ids in groups.items():
        open_issue('Cuarentena: ' + why[:120], f'{len(ids)} libros apartados en la carga del {datetime.now(ZoneInfo("Europe/Madrid")):%Y-%m-%d}: '
                   + ', '.join(f'`{i}`' for i in ids[:30]) + (' …' if len(ids) > 30 else ''))


def open_issue(title, body):
    """Abre la issue `fallo` con ese título, o comenta en la abierta: una por causa, no una por noche.

    Un fallo al crearla no tumba la carga (ya se publicó lo válido); queda el aviso en el log."""
    def gh(*args):
        return subprocess.run([shutil.which('gh') or 'gh', *args], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', check=True).stdout
    try:
        gh('label', 'create', 'fallo', '--color', 'B60205', '--description', 'Fallo detectado por un empleado automático', '--force')
        query = title.replace('"', ' ')  # unas comillas en la causa romperían la búsqueda literal
        found = gh_listas.lista(gh, 'issue', 'list', '--state', 'open', '--label', 'fallo',
                                '--search', f'"{query}" in:title', '--json', 'number,title', tope=1000)
        same = [i for i in found if i['title'] == title]
        if same:
            seen = json.loads(gh('issue', 'view', str(same[0]['number']), '--json', 'body,comments'))
            # Un reintento de la misma carga (código 75) repite el mismo texto: no se comenta dos veces.
            if body != seen.get('body') and all(c.get('body') != body for c in seen.get('comments', [])):
                gh('issue', 'comment', str(same[0]['number']), '--body', body)
        else:
            gh('issue', 'create', '--title', title, '--label', 'fallo', '--body', body)
    except (subprocess.CalledProcessError, OSError, ValueError) as exc:
        print(f'::warning::No se pudo abrir la issue «{title}»: {exc}', flush=True)


def data_contract_failures():
    """Corre los contratos de datos; devuelve sus fallos ([{test, texto}], vacío si pasan)."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'fallos.json'
        code = subprocess.run([sys.executable, 'scripts/check-reading-data.py', '--fallos', str(out)], cwd=ROOT).returncode
        failures = json.loads(out.read_text(encoding='utf-8')) if out.exists() else []
    if code and not failures:
        raise RuntimeError(f'check-reading-data salió con {code} sin fallos de contrato (error de carga de los tests)')
    return failures


def entradas(quarantined, ids):
    """Lo que la cuarentena dice de esos libros, comparable entre vueltas del bucle de assemble().

    Sin los contadores: apply() suma un intento cada vez que la llama, también dentro de la misma noche."""
    ids, contadores = set(ids), {'intentos', 'ultimo_intento'}
    return sorted(json.dumps({k: v for k, v in h.items() if k not in contadores}, sort_keys=True, ensure_ascii=False,
                             default=str) for h in quarantined if h['libro']['id'] in ids)


def drop_orphan_pages(quarantined):
    """La página de un libro nuevo apartado ya se generó y registró: el builder no borra, así que se quita aquí."""
    live = {b['slug'] for b in read_json(ROOT / reading_quarantine.CATALOGUE)['libros']}
    for h in quarantined:
        slug = h['libro'].get('slug')
        page = f'recomendaciones/libros/{slug}/index.html'
        if slug and slug not in live and not subprocess.run(['git', 'cat-file', '-e', 'HEAD:' + page], cwd=ROOT).returncode == 0:
            subprocess.run(['git', 'rm', '-q', '--cached', '--ignore-unmatch', '--', page], cwd=ROOT, check=True)
            (ROOT / page).unlink(missing_ok=True)
    # Las páginas derivadas (continuaciones del catálogo, autores, sellos) que el intento fallido generó y nunca se
    # publicaron también sobran: el builder las rechaza como huérfanas y un solo libro apartado pararía el lote.
    for folder in ('recomendaciones/pagina', 'recomendaciones/autores', 'recomendaciones/autores/pagina', 'recomendaciones/editoriales'):
        for path in sorted((ROOT / folder).glob('*/index.html')):
            rel = path.relative_to(ROOT).as_posix()
            if subprocess.run(['git', 'cat-file', '-e', 'HEAD:' + rel], cwd=ROOT).returncode != 0:
                subprocess.run(['git', 'rm', '-q', '--cached', '--ignore-unmatch', '--', rel], cwd=ROOT, check=True)
                path.unlink(missing_ok=True)


def assemble(report, *, changed, replaced=None, source=None, checkpoint=None):
    """Reconstruye todo lo derivado sobre el checkout actual, abre la PR y la publica por main protegido."""
    changed_ratings = changed
    # Un libro que incumple el contrato sale del lote (o vuelve a su versión publicada) en vez de pararlo.
    held_path = ROOT / reading_quarantine.QUARANTINE
    held_before = {h['libro']['id'] for h in read_json(held_path)['libros']} if held_path.exists() else set()
    quarantined = reading_quarantine.apply(ROOT)
    # Una regla corregida libera libros apartados: eso también se publica, aunque no haya novedades.
    released = held_before - {h['libro']['id'] for h in quarantined}
    # A scheduled RSS item can become due without a new book or rating. Build
    # current pages first, then advance feeds inside this SAME daily writer.
    command(sys.executable, 'scripts/build-reading-catalogue.py')
    rss_config=read_json(ROOT / 'data/reading-pinterest-boards.json')
    command(sys.executable, 'scripts/build-reading-pinterest-rss.py', *(['--assign'] if rss_config.get('rss_enabled') else []))
    rss_changed=bool(subprocess.check_output(['git','status','--porcelain','--untracked-files=all','--','assets/pinterest/feeds','data/reading-pinterest-state.json'],cwd=ROOT,text=True).strip())
    # Una reparación de la cuarentena (clasificación, retirada de no-libros) también se publica sin novedades.
    repaired = bool(subprocess.check_output(['git', 'status', '--porcelain', '--', reading_quarantine.CATALOGUE, 'recomendaciones/libros'], cwd=ROOT, text=True).strip())
    if not (report['new_books'] or report['updated_books'] or released or changed_ratings or report['stats'].get('author_profiles_updated') or rss_changed or repaired):
        drop_checkpoint(checkpoint)
        return
    # Un contrato de datos que nombra libros (p. ej. una sinopsis que empieza gritando) los aparta y se reconstruye;
    # si un fallo no nombra ningún libro, o vuelve a señalar los mismos, es una regla rota y la carga para (10/11).
    # La cuarentena solo existe si alguna vez apartó un libro: git add falla con una ruta que no existe.
    staged = ('assets/page-order.generated.js', 'assets/reading-market.json', 'data/reading-catalogue.json', 'data/reading-authors.json', 'data/reading-publishers.json', 'data/reading-intake-state.json',
              'data/reading-quarantine.json', 'data/content-registry.json', 'assets/reading-covers', 'assets/reading-audio', 'recomendaciones', 'editoriales', 'editoriales-sitemap.xml', 'mapa-del-sitio/index.html')
    # Register new routes before builders that deliberately consume git ls-files.
    def registrar(_root):
        git_estado.preparar(ROOT, [*staged, 'assets/pinterest/feeds'])
    flagged = {}
    # Sin tope de rondas: cada vuelta o pasa, o para (no nombra libros nuevos ni la cuarentena hace nada con los ya
    # nombrados), o avanza; con 1000 altas por tanda caben más de 3 tandas de problemas encadenados, y el catálogo
    # es finito. Un libro repetido no es automáticamente «la regla rota»: 16/11, isbn-9791388205675 volvía a
    # nombrarse en la segunda ronda porque la primera solo pudo revertirlo (había cambiado un dato ajeno al
    # contrato, como la fecha del barrido de precios) sin arreglar el motivo; revertirlo lo deja idéntico a su
    # versión publicada, y esa segunda ronda es la que la cuarentena por fin puede apartar de verdad (isolate()
    # la retira). Solo para si, además de repetirse, la cuarentena no mueve nada (como hacía antes de verificar).
    while True:
        # Misma cadena que rebase-regenerando y merge-main (scripts/materializar_generados.py).
        materializar.construir(ROOT, antes_de_indexar=registrar)
        materializar.comprobar(ROOT, assets=False)
        # Solo los contratos de datos: el código ya lo probó la batería completa del Required merge gate en main.
        failures = data_contract_failures()
        if not failures:
            break
        named, unattributed = reading_quarantine.split_flagged(failures, read_json(ROOT / reading_quarantine.CATALOGUE))
        if not named:
            raise RuntimeError('check-reading-data falló en contratos que no nombran ningún libro: '
                               + '; '.join(f['test'] for f in unattributed)[:600])
        if unattributed:
            # Se apartan primero los nombrados y se repite: el fallo sin libro suele ser consecuencia de ellos.
            print('Contratos sin libro (se reintentan tras apartar los nombrados): '
                  + '; '.join(f['test'] for f in unattributed)[:600], flush=True)
        repeated = set(named) <= set(flagged)
        flagged.update(named)
        antes = entradas(quarantined, named)
        quarantined = reading_quarantine.apply(ROOT, flagged=flagged)
        # No basta con que la cuarentena mueva algo: puede estar moviendo libros de noches anteriores sin
        # relación con los que se repiten aquí. Ni basta con que los repetidos estén en ella: si ya lo estaban
        # igual en la vuelta anterior, nada cambió y la siguiente vuelta sería idéntica hasta el timeout del job
        # (R3-08 GPT, 25/11). Solo es avance que cambie la entrada de algún repetido (revertido → retirado, 16/11).
        if repeated and entradas(quarantined, named) == antes:
            raise RuntimeError('check-reading-data falló en contratos que no se resuelven apartando libros: '
                               + '; '.join(f['test'] for f in failures)[:600])
        released = held_before - {h['libro']['id'] for h in quarantined}
        drop_orphan_pages(quarantined)
    quarantine_alert(report, quarantined)
    command('git', 'diff', '--check')
    paths = git_estado.rutas(ROOT)
    if not paths or any(not publisher.allowed_path(p) for p in paths):
        raise ValueError('Cambios fuera de los artefactos permitidos: ' + str([p for p in paths if not publisher.allowed_path(p)]))
    git_estado.preparar(ROOT, paths)
    day = datetime.now(ZoneInfo('Europe/Madrid')).date().isoformat()
    branch = publisher.publication.fresh_branch('automation/reading-catalogue-' + day + '-', cwd=ROOT)
    bot_identity()
    command('git', 'switch', '-c', branch)
    command('git', 'commit', '-m', 'Actualizar catálogo de lectura ' + day)
    # Las portadas nuevas deben estar en el almacén antes de que la PR pueda fusionarse (sin almacén activo: no-op).
    print(f'Portadas subidas al almacén: {cover_store.flush("Portadas de la carga " + day)}', flush=True)
    push('HEAD:refs/heads/' + branch)
    if replaced:
        # Antes de abrir la nueva: nunca quedan dos cargas abiertas. Si algo falla después, las dos ramas siguen en origin.
        publisher.close_proposal(replaced, f'main avanzó durante su CI. Sus datos fuente (libros, pendientes, precios y cuarentena) '
                                 f'pasan sin nueva consulta a `{branch}`, reconstruida sobre el main actual. Se conserva la rama `{source}`.')
    body = ROOT / '.ci/reading-intake/pr-body.md'
    body.parent.mkdir(parents=True, exist_ok=True)
    body.write_text((f'Sustituye a #{replaced}: mismos datos consultados, trasladados al main actual y con páginas e índices regenerados.\n\n'
                     if replaced else '') + 'Incorpora ' + str(len(report['new_books'])) + ' ediciones verificadas en sus fichas editoriales oficiales.\n\n'
                    'Carga sin LLM ni API de pago; portadas optimizadas, ISBN comprobados, autores y enlaces internos generados. '
                    'No importa precios ni valoraciones sin un proveedor autorizado. Los candidatos incompletos quedan pendientes.\n\n'
                    + quarantine_alert_note()
                    + quarantine_summary(quarantined, released) +
                    'Se ejecutan las pruebas reales del commit y las reglas de main antes de fusionar. Después se despliega y se comprueba producción.\n', encoding='utf-8')
    publisher.publication.gh('pr', 'create', '--base', 'main', '--head', branch,
                             '--title', 'Actualizar catálogo de lectura ' + day, '--body-file', str(body))
    # La PR puede cerrarse por CI rojo: conservar la copia hasta comprobar publicación y Pages.
    publisher.run(branch)
    drop_checkpoint(checkpoint)


def main(publish):
    try:
        refresh(publish=publish)
    except publisher.publication.StaleMerge as exc:
        # The stale bot PR is closed and regenerated by the next invocation.
        print(exc, flush=True)
        sys.exit(publisher.publication.STALE_EXIT_CODE)
    except publisher.publication.PrAbierta as exc:
        # La PR de datos sigue abierta con su CI en marcha: la reanuda la siguiente carga. Se conserva el punto de
        # guardado, así la cadena nocturna sigue (checkpoints_restantes) y la reanudación fusiona sin volver a consultar.
        print(f'::warning::{exc}; la siguiente carga reanuda la PR', flush=True)
        chain_report(0, pr_abierta=str(exc))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    main(args.publish)
