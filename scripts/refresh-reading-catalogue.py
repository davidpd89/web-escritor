#!/usr/bin/env python3
"""Single writer for free, bounded publisher intake and generated-only PRs."""
import argparse
import importlib.util
import json
import os
import subprocess
import urllib.request
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import reading_quarantine
import catalogo_estado as estado
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
                'data/reading-publishers.json', 'data/reading-intake-state.json', 'data/reading-quarantine.json', 'assets/reading-covers', 'assets/reading-audio')


def command(*args):
    subprocess.run(args, cwd=ROOT, check=True)


def git(*args, root=ROOT, data=None):
    return subprocess.run(['git', *args], cwd=root, check=True, capture_output=True, input=data).stdout


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


def carry(branch, root=ROOT):
    """Datos fuente de una PR verde pero obsoleta, sobre el main actual y sin volver a consultar las fuentes.

    Devuelve los id de libro nuevos frente a main, o None si sus datos fuente chocan con main (entonces se
    regenera desde las fuentes). Libros válidos, pendientes, precios y cuarentena viajan juntos en SOURCE_PATHS.
    """
    git('fetch', '--quiet', 'origin', 'main', f'+refs/heads/{branch}:refs/remotes/origin/{branch}', root=root)
    head, latest = (git('rev-parse', ref, root=root).decode().strip() for ref in ('origin/' + branch, 'origin/main'))
    base = git('merge-base', latest, head, root=root).decode().strip()
    patch = git('diff', '--binary', base, head, '--', *SOURCE_PATHS, root=root)
    before = catalogue_ids(git('show', latest + ':data/reading-catalogue.json', root=root))
    if not patch or not replay(patch, latest, root):
        return None
    return sorted(catalogue_ids((root / 'data/reading-catalogue.json').read_bytes()) - before)


def bot_identity(root=ROOT):
    git('config', 'user.name', 'github-actions[bot]', root=root)
    git('config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com', root=root)


def save_checkpoint(day, root=ROOT):
    """Sube a una rama propia los datos fuente recién consultados, antes de construir páginas y de las pruebas.

    Si algo falla después (una prueba, un generador, el límite de tiempo del job), la siguiente ejecución los
    publica con `carry` sin repetir la ingesta. Usa un índice temporal: ni HEAD ni el índice real cambian.
    """
    paths = [p for p in SOURCE_PATHS if (root / p).exists()]
    index = root / git('rev-parse', '--git-path', 'checkpoint-index', root=root).decode().strip()
    env = {**os.environ, 'GIT_INDEX_FILE': str(index)}
    try:
        for args in (('read-tree', 'HEAD'), ('add', '--', *paths)):
            subprocess.run(['git', *args], cwd=root, check=True, capture_output=True, env=env)
        tree = subprocess.run(['git', 'write-tree'], cwd=root, check=True, capture_output=True, text=True, env=env).stdout.strip()
    finally:
        index.unlink(missing_ok=True)
    if tree == git('rev-parse', 'HEAD^{tree}', root=root).decode().strip():
        return None
    bot_identity(root)
    commit = git('commit-tree', tree, '-p', 'HEAD', '-m', 'Datos consultados de la carga ' + day, root=root).decode().strip()
    branch = publisher.publication.fresh_branch(CHECKPOINT_PREFIX + day + '-', cwd=root)
    git('push', '--quiet', 'origin', f'{commit}:refs/heads/{branch}', root=root)
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


def pending_batches(opened):
    """Cargas del propio escritor; las PR de textos las regenera su bucle y no frenan los libros."""
    return [p['headRefName'] for p in opened if p['headRefName'].startswith('automation/reading-catalogue-')
            and not p['headRefName'].startswith(TEXTS_PREFIX)]


def refresh(*, publish=False):
    config = read_json(ROOT / 'data/reading-intake-config.json')
    if publish and subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=all'], cwd=ROOT, text=True).strip():
        raise ValueError('La publicación automática exige un checkout limpio')
    if publish and not config.get('autopublish'):
        raise ValueError('Autopublicación desactivada en la configuración')
    # A failed previous batch stays inspectable; never pile up duplicate writers.
    opened = json.loads(publisher.publication.gh('pr', 'list', '--state', 'open', '--base', 'main', '--limit', '100', '--json', 'headRefName'))
    pending = pending_batches(opened)
    if pending:
        if len(pending) != 1:
            raise ValueError('Hay varias cargas pendientes; revisar antes de continuar')
        action = publisher.resume_pending(pending[0]) if publish else 'resumed'
        if action == 'resumed':
            print('Carga pendiente conservada: ' + pending[0])
            return
        if action == 'carry':
            replaced = json.loads(publisher.publication.gh('pr', 'view', pending[0], '--json', 'number'))['number']
            carried = carry(pending[0])
            if carried is not None:
                print(f'Datos de #{replaced} trasladados a main sin nueva consulta: {len(carried)} libros nuevos', flush=True)
                return assemble({'new_books': carried, 'updated_books': [], 'stats': {}}, changed=True,
                                replaced=replaced, source=pending[0])
            publisher.close_proposal(replaced, 'Sus datos fuente chocan con cambios nuevos de main. Se conserva esta propuesta y su rama '
                                     'como referencia; el escritor vuelve a consultar las fuentes y regenera el lote desde main.')
    if publish:
        # Una ejecución anterior consultó y no llegó a abrir PR: se publica eso, sin consultar de nuevo.
        for saved in checkpoints():
            carried = carry(saved)
            if carried is None:
                print(f'{saved}: ya está en main o choca con él; se descarta', flush=True)
                drop_checkpoint(saved)
                continue
            print(f'Datos de {saved} recuperados sin nueva consulta: {len(carried)} libros nuevos', flush=True)
            # La cadena nocturna lee stats.accepted: un lote recuperado también encadena el siguiente.
            write_if_changed(ROOT / '.ci/reading-intake/publisher-report.json',
                             {'recuperado_de': saved, 'new_books': carried, 'stats': {'accepted': len(carried)}})
            return assemble({'new_books': carried, 'updated_books': [], 'stats': {}}, changed=True, checkpoint=saved)
    amazon = config.get('amazon_catalogo', {}).get('enabled')
    failure = None
    if amazon and publish:
        # Un fallo de las altas no puede dejar la noche sin precios ni portadas (09/11: un ISBN repetido tumbó
        # refresh() antes de market_refresh). Se deshacen sus escrituras, siguen precios y portadas y al final se
        # sale con error para que el fallo siga a la vista (y lo recoja la autorreparación nocturna).
        try:
            report = amazon_intake(config, publish)
        except Exception as exc:  # noqa: BLE001
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
    changed = market_refresh(config)
    follow_main()
    day = datetime.now(ZoneInfo('Europe/Madrid')).date().isoformat()
    saved = save_checkpoint(day)
    health_report(config)
    if amazon and not failure:
        # Solo ahora: los libros ya están a salvo en la rama de datos (o no había nada), así que la cola de
        # semillas puede avanzar sin perder ninguno si después falla la PR.
        estado.guardar(f'Estado de la ingesta {day}: {len(report["new_books"])} altas')
    result = assemble(report, changed=changed, checkpoint=saved)
    if failure:
        raise RuntimeError('Las altas de Amazon fallaron; precios y portadas sí se publicaron') from failure
    return result


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
    # La prueba solo comprueba credenciales y fuentes con unas pocas peticiones: ni transforma ni gasta cuota.
    phase, requests = ('todo', int(settings.get('peticiones', 600))) if publish else ('descargar', 20)
    import catalogo_amazon
    code = catalogo_amazon.main([phase, '--dia', day, '--peticiones', str(requests),
                          '--altas', str(int(settings.get('altas', 200)))])
    new = sorted(catalogue_ids(catalogue_path.read_bytes()) - before)
    summary = read_json(catalogo_amazon.WORK / f'informe-{day}.json', {})
    if code:
        # Libros vaciados o desaparecidos respecto a la foto anterior. No lo causa la ingesta (solo añade y enlaza);
        # abortar dejaría la foto vieja en catalogo-estado y bloquearía todas las noches siguientes. Se avisa.
        print('::warning::Revisión del catálogo: campos vaciados o libros desaparecidos respecto a la foto anterior; '
              'ver .ci/reading-intake/amazon-catalogo.json', flush=True)
    write_if_changed(ROOT / '.ci/reading-intake/amazon-catalogo.json', summary)
    return {'new_books': new, 'updated_books': [], 'stats': {'accepted': len(new), 'fuente': 'amazon_catalogo',
                                                               'regresion': bool(code)}}


def market_refresh(config):
    """Valoraciones, formatos, portadas y precios: devuelve si cambió algún dato publicado."""
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
    if not (report['new_books'] or report['updated_books'] or released or changed_ratings or report['stats'].get('author_profiles_updated') or rss_changed):
        drop_checkpoint(checkpoint)
        return
    # Register new routes before builders that deliberately consume git ls-files.
    command(sys.executable, 'scripts/build-reading-catalogue.py')
    command(sys.executable, 'scripts/build-editoriales.py', '--data', 'data/editoriales.json', '--output', '.')
    command(sys.executable, 'scripts/build-page-order.py')
    # La cuarentena solo existe si alguna vez apartó un libro: git add falla con una ruta que no existe.
    staged = ('assets/page-order.generated.js', 'assets/reading-market.json', 'data/reading-catalogue.json', 'data/reading-authors.json', 'data/reading-publishers.json', 'data/reading-intake-state.json',
              'data/reading-quarantine.json', 'data/content-registry.json', 'assets/reading-covers', 'assets/reading-audio', 'recomendaciones', 'editoriales', 'editoriales-sitemap.xml', 'mapa-del-sitio/index.html')
    command('git', 'add', '--', *[p for p in staged if (ROOT / p).exists()])
    command('git','add','--','assets/pinterest/feeds')
    for script in ('build-site-shell.py', 'build-sitemap.py', 'build-pagefind-index.py'):
        command(sys.executable, 'scripts/' + script)
    for script in ('build-reading-catalogue.py', 'build-page-order.py', 'build-site-shell.py', 'build-sitemap.py', 'build-pagefind-index.py'):
        command(sys.executable, 'scripts/' + script, '--check')
    # Solo los contratos de datos: el código ya lo probó la batería completa del Required merge gate en main.
    command(sys.executable, 'scripts/check-reading-data.py')
    command('git', 'diff', '--check')
    changed = subprocess.check_output(
        ['git', 'status', '--porcelain', '--untracked-files=all'], cwd=ROOT, text=True)
    paths = [line[3:] for line in changed.splitlines()]
    if not paths or any(not publisher.allowed_path(p) for p in paths):
        raise ValueError('Cambios fuera de los artefactos permitidos: ' + str([p for p in paths if not publisher.allowed_path(p)]))
    command('git', 'add', '--', *paths)
    day = datetime.now(ZoneInfo('Europe/Madrid')).date().isoformat()
    branch = publisher.publication.fresh_branch('automation/reading-catalogue-' + day + '-', cwd=ROOT)
    bot_identity()
    command('git', 'switch', '-c', branch)
    command('git', 'commit', '-m', 'Actualizar catálogo de lectura ' + day)
    command('git', 'push', 'origin', 'HEAD:refs/heads/' + branch)
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
                    + quarantine_summary(quarantined, released) +
                    'Se ejecutan las pruebas reales del commit y las reglas de main antes de fusionar. Después se despliega y se comprueba producción.\n', encoding='utf-8')
    publisher.publication.gh('pr', 'create', '--base', 'main', '--head', branch,
                             '--title', 'Actualizar catálogo de lectura ' + day, '--body-file', str(body))
    # Desde aquí los datos viven en la rama de la PR (resume_pending/carry los recuperan si su CI falla).
    drop_checkpoint(checkpoint)
    publisher.run(branch)


def main(publish):
    try:
        refresh(publish=publish)
    except publisher.publication.StaleMerge as exc:
        # The stale bot PR is closed and regenerated by the next invocation.
        print(exc, flush=True)
        sys.exit(publisher.publication.STALE_EXIT_CODE)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    main(args.publish)
