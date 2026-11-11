#!/usr/bin/env python3
"""Autorreparación de los flujos programados (David, 09/11/2026).

Se ejecuta cada hora desde el Programador de tareas de Windows del equipo de David (no en Actions: necesita las sesiones
de los CLI). Para cada flujo vigilado mira la última ejecución en main:

1. Falla por primera vez → la relanza una vez sobre main (`gh workflow run`): lo pasajero o ya arreglado se cura solo.
2. Vuelve a fallar → crea un worktree limpio desde origin/main, le da el registro del fallo a una IA y le pide la causa
   raíz con su prueba. Rotación: Claude (cuenta del sistema) → Claude cuenta 2 (CLAUDE_CONFIG_DIR) → Codex; si una
   responde que no le queda cuota pasa a la siguiente, y si una no deja cambios válidos también.
3. Con cambios: puerta local (`local-ci.py --baseline`), commit, PR con auto-merge.
4. Cuando la PR entra en main, relanza el flujo y deja de vigilar ese fallo cuando sale verde.

Por método (11/11: dos arreglos seguidos sobre una hipótesis falsa, tres noches de textos sin publicar y nadie se enteró):
- Cada intento queda en un historial que recibe el siguiente agente: si un arreglo ya entró en main y el fallo se repite,
  se le dice que la premisa era falsa. También recibe el estado real (PR abiertas con su rama y autor, últimas
  ejecuciones, últimos commits de main): sin gh no podía verlo y adivinaba.
- Las publicaciones locales (textos, auditoría de Amazon) se vigilan igual que los workflows (scripts/estado_local.py).
- Una PR de reparación que no puede entrar (CI rojo) se cierra y cuenta como intento fallido, en vez de esperar siempre.
- Al agotar los intentos del día se abre (o se comenta) una issue y salta un aviso en el escritorio.

Excepción explícita a «no mergear de 00:00 a 06:00»: David pidió reparar y relanzar la nocturna sin esperar. Sí respeta
«no mergear durante la ingesta»: si la carga del catálogo está en marcha, la PR espera a la siguiente pasada.

Uso: python scripts/night-autorepair.py [--dry-run] [--solo FLUJO.yml]
Tarea: scripts/night-autorepair.cmd, cada hora (schtasks /Create /TN web-escritor-autorepair /SC HOURLY /TR <ruta .cmd> /IT).
"""
from __future__ import annotations

import argparse, datetime as dt, json, os, re, shutil, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import estado_local  # noqa: E402

# El Programador de tareas ejecuta la copia de origin/main (ver night-autorepair.cmd); el repo vivo se indica aparte.
REPO = Path(os.environ.get('AUTOREPAIR_REPO') or Path(__file__).resolve().parents[1])
GH_REPO = 'davidpd89/web-escritor'
ESTADO_DIR = estado_local.ESTADO_DIR   # %LOCALAPPDATA%/web-escritor-autorepair
WT_BASE = Path(os.environ.get('AUTOREPAIR_WT_BASE') or REPO.parent)
VIGILADOS = (
    'reading-catalogue-sync.yml', 'atlas-directory-sync.yml', 'reading-telegram-publish.yml', 'postdeploy-deep-audit.yml',
    'radar-clock-refresh.yml', 'radar-source-monitor.yml', 'production-smoke-monitor.yml', 'broken-links.yml', 'weekly-full-audit.yml',
)
INGESTA = 'reading-catalogue-sync.yml'
LOCAL = 'local:'         # flujos que corren en este equipo; su estado lo deja scripts/estado_local.py
PR_BLOQUEADA_MIN = 30    # todas las comprobaciones acabadas en rojo durante 30 min: la PR no va a entrar
PR_CADUCA_H = 4          # una PR de reparación que no entra en 4 h no va a entrar
HISTORIAL_MAX = 10
VENTANA_H = 36           # fallos más viejos no se tocan: otra ejecución posterior ya habrá dicho algo
MAX_INTENTOS_DIA = 3     # reparaciones con IA por flujo y día; cada una sabe qué falló en las anteriores
LIMITE = re.compile(r"usage limit|hit your limit|limit reached|rate.?limit|out of (extra )?usage|credit balance|quota|\b429\b", re.I)
# Un «arreglo» que solo apaga el síntoma no vale: se rechaza el diff y se prueba con la siguiente IA.
PROHIBIDO = re.compile(r"^\+.*(continue-on-error:\s*true|\|\|\s*true\b|@pytest\.mark\.skip|\.skip\(|test\.skip|xfail)", re.M)
TRAILER_CLAUDE = 'Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>'
PIE_PR = '🤖 Generated with [Claude Code](https://claude.com/claude-code)'
SIN_VENTANA = 0x08000000 if os.name == 'nt' else 0


def agentes(cuenta2: Path | None = None):
    """Orden de rotación. Cada agente: (nombre, argv sin el prompt, entorno extra, trailer)."""
    cuenta2 = cuenta2 or Path.home() / '.claude-cuenta2'
    claude = ['claude', '-p', '--permission-mode', 'bypassPermissions', '--output-format', 'text', '--max-turns', '200']
    lista = [('claude', claude, {}, TRAILER_CLAUDE)]
    if cuenta2.is_dir():
        lista.append(('claude-cuenta2', claude, {'CLAUDE_CONFIG_DIR': str(cuenta2)}, TRAILER_CLAUDE))
    lista.append(('codex', ['codex', 'exec', '--dangerously-bypass-approvals-and-sandbox', '--ephemeral'], {}, ''))
    return lista


def decidir(run: dict | None, previo: dict | None, ahora: dt.datetime, intentos_hoy: int, infra: bool = False) -> str:
    """Qué hacer con la última ejecución de un flujo. Pura, para poder probarla.

    `infra`: el fallo es de GitHub (caída de Actions, ejecución sin trabajos), no del código. Eso nunca se
    «repara» con IA: se reintenta cada hora hasta que GitHub vuelva.

    Devuelve: 'nada', 'olvidar' (salió verde: se borra el estado), 'relanzar', 'reparar', 'esperar_pr', 'agotado'."""
    if not run or run.get('status') != 'completed':
        return 'nada'
    if run.get('conclusion') in ('success', 'skipped'):
        return 'olvidar' if previo else 'nada'
    if run.get('conclusion') not in ('failure', 'timed_out', 'startup_failure'):
        return 'nada'   # cancelled: alguien lo paró a propósito
    creado = dt.datetime.fromisoformat(run['createdAt'].replace('Z', '+00:00'))
    if ahora - creado > dt.timedelta(hours=VENTANA_H):
        return 'nada'
    previo = previo or {}
    if infra:
        relanzado = previo.get('relanzado')
        if relanzado and ahora - dt.datetime.fromisoformat(relanzado) < dt.timedelta(minutes=50):
            return 'nada'
        return 'relanzar'
    if previo.get('pr') and not previo.get('pr_cerrada'):
        return 'esperar_pr'
    # Se relanza con un dispatch nuevo sobre main (no `rerun`, que repite el commit viejo y volvería a fallar por
    # algo que quizá ya está arreglado). Hasta que aparece esa ejecución nueva, se espera.
    relanzado = previo.get('relanzado')
    if not relanzado:
        return 'relanzar'
    if creado <= dt.datetime.fromisoformat(relanzado):
        return 'relanzar' if ahora - dt.datetime.fromisoformat(relanzado) > dt.timedelta(hours=3) else 'nada'
    if intentos_hoy >= MAX_INTENTOS_DIA:
        return 'agotado'
    return 'reparar'


CARGA_PERDIDA_DESDE_H = 1  # UTC; el cron es a las 00:17


def carga_perdida(ultima: dict | None, ahora: dt.datetime, lanzada_hoy: bool) -> bool:
    """El cron de la carga (00:17 UTC) no llegó a crear ejecución: GitHub a veces se salta crons, sobre todo en
    incidencias. A partir de las 01:00 UTC, si hoy no hay ninguna carga, se lanza una (una vez al día). Con 02:00 la
    carga del 2026-11-10 no salió hasta la pasada de las 02:20 UTC: una hora menos de margen hasta las 06:00 Madrid."""
    if lanzada_hoy or ahora.hour < CARGA_PERDIDA_DESDE_H:
        return False
    if not ultima:
        return True
    creado = dt.datetime.fromisoformat(ultima['createdAt'].replace('Z', '+00:00'))
    return creado.date() < ahora.date()


def sin_cuota(salida: str) -> bool:
    return bool(LIMITE.search(salida or ''))


def diff_valido(diff: str) -> tuple[bool, str]:
    if not diff.strip():
        return False, 'sin cambios'
    m = PROHIBIDO.search(diff)
    if m:
        return False, 'apaga el síntoma en vez de arreglarlo: ' + m.group(0)[:120]
    return True, ''


def es_local(flujo: str) -> bool:
    return flujo.startswith(LOCAL)


def describir(flujo: str, run: dict) -> str:
    if es_local(flujo):
        comando = ' '.join(Path(a).name if i < 3 else a for i, a in enumerate(run.get('argv') or []))
        return (f"La publicación local `{flujo.removeprefix(LOCAL)}` (corre en el equipo de David: `{comando}`; "
                f"registro en {run.get('url')})")
    return f"El flujo programado `.github/workflows/{flujo}` (ejecución {run.get('url')})"


def historial_texto(historial: list[dict] | None) -> str:
    """Lo que ya se intentó con este mismo fallo, para que el siguiente agente no repita una hipótesis falsa."""
    if not historial:
        return ''
    lineas = []
    for h in historial[-6:]:
        pr = f"PR #{h['pr']} «{h.get('titulo', '')}»" if h.get('pr') else h.get('titulo', '')
        lineas.append(f"- {h.get('fecha', '')[:16]} {h.get('agente', '?')}: {pr} → {h.get('resultado', '')}")
    aviso = ''
    if any(h.get('resultado', '').startswith('mergeada') for h in historial):
        aviso = ("\nUn arreglo anterior YA ESTÁ EN MAIN y el fallo se repitió: su hipótesis era falsa o incompleta. "
                 "No la repitas ni la refuerces. Vuelve a la premisa: contrasta el registro con el estado real de abajo "
                 "(PR abiertas, ramas, autores, commits) y busca qué otra cosa produce exactamente este error.")
    if any(h.get('resultado', '').startswith('CI rojo') for h in historial):
        aviso += "\nUn arreglo anterior no pasó el CI de su PR: el tuyo tiene que pasar también esas comprobaciones."
    return "\n\n## Intentos anteriores de este mismo fallo\n" + '\n'.join(lineas) + aviso


def prompt_reparacion(flujo: str, run: dict, registro: str, historial: list[dict] | None = None, estado: str = '') -> str:
    return f"""Eres el turno de noche del repositorio web-escritor (sitio estático de David Porto, desplegado desde main).
{describir(flujo, run)} ha fallado dos veces seguidas con el código de main (la segunda tras relanzarlo).

Últimas líneas del registro del fallo:
```
{registro}
```

{historial_texto(historial)}{estado}

Tarea: encuentra la causa raíz y arréglala de forma definitiva en este worktree (rama nueva desde origin/main).
- Arregla la clase de fallo, no el caso: si el error viene de una suposición (un prefijo de rama, un formato de dato, un
  límite de longitud), corrige la suposición para todos los casos parecidos, no solo para el que salió hoy.
- Reproduce el fallo en local y añade o ajusta una prueba en tests/ o qa/ que falle sin tu arreglo y pase con él.
- Ejecuta las comprobaciones relacionadas con lo que toques y confirma que pasan.
- Prohibido: desactivar o saltar pruebas, `continue-on-error`, `|| true`, subir umbrales para que pase, tocar secretos,
  borrar datos del catálogo para esquivar el error. Un reintento solo vale si el fallo es de red y ya hay prueba de ello.
- Si de verdad no hay arreglo en el código (caída de un servicio externo, credencial caducada), NO cambies nada y escribe
  el motivo en AUTOREPAIR_NOFIX.md.
- No hagas commit ni push: el turno de noche lo hace tras pasar la puerta local.
- Al terminar escribe AUTOREPAIR_SUMMARY.md: primera línea = título corto del commit en español; después causa, arreglo y
  comprobaciones hechas (comandos y resultado).
Responde siempre en español."""


def prompt_continuar(prompt: str, agente: str, puerta: str) -> str:
    base = prompt.split('\n\n## Intento anterior')[0]
    return base + f"""

## Intento anterior ({agente})
Su arreglo sigue en el worktree (mira `git diff`). La puerta local lo rechazó con esto:
```
{puerta[-2500:]}
```
Parte de ese arreglo: corrígelo o complétalo; no lo rehagas desde cero salvo que esté mal. Si los fallos no tienen que ver
con lo cambiado (puertos, servidores, entorno), explícalo en AUTOREPAIR_SUMMARY.md con la prueba de que también fallan en main."""


# --- efectos (gh, git, CLIs) ---------------------------------------------------------------------------------------

def sh(args, cwd=REPO, timeout=600, env=None, check=False, entrada=None):
    r = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout,
                       env={**os.environ, **(env or {})}, input=entrada, creationflags=SIN_VENTANA)
    if check and r.returncode:
        raise RuntimeError(f"{' '.join(map(str, args[:4]))}… → {r.returncode}: {(r.stderr or r.stdout)[-400:]}")
    return r


def exe(nombre):
    return shutil.which(nombre + '.cmd') or shutil.which(nombre) or nombre


def gh_json(*args):
    r = sh(['gh', *args, '--repo', GH_REPO], check=True)
    return json.loads(r.stdout or 'null')


def flujos_locales(carpeta: Path | None = None) -> list[str]:
    carpeta = carpeta or estado_local.LOCALES
    return sorted(LOCAL + p.stem for p in carpeta.glob('*.json')) if carpeta.is_dir() else []


def ultima_ejecucion(flujo):
    if es_local(flujo):
        return estado_local.leer(flujo.removeprefix(LOCAL))
    runs = gh_json('run', 'list', '--workflow', flujo, '--branch', 'main', '--limit', '1',
                   '--json', 'databaseId,status,conclusion,attempt,url,createdAt,event')
    return runs[0] if runs else None


def actions_caido():
    """Descripción de la incidencia si GitHub Actions no está operativo; None si va bien o no se puede saber."""
    import urllib.request
    try:
        with urllib.request.urlopen('https://www.githubstatus.com/api/v2/summary.json', timeout=20) as r:
            datos = json.load(r)
    except Exception:
        return None
    for c in datos.get('components', []):
        if c.get('name') == 'Actions' and c.get('status') not in ('operational', None):
            return c['status']
    return None


def fallo_de_infraestructura(run_id) -> bool:
    """Una ejecución fallida sin trabajos, o cuyos trabajos fallaron sin llegar a ejecutar ningún paso, es GitHub
    (caída, «workflow file issue» durante incidencias, runner perdido), no el código."""
    try:
        jobs = gh_json('run', 'view', str(run_id), '--json', 'jobs')['jobs']
    except Exception:
        return False
    fallidos = [j for j in jobs if j.get('conclusion') in ('failure', 'timed_out', 'startup_failure', None)]
    if not jobs:
        return True
    return bool(fallidos) and all(not any(s.get('conclusion') == 'failure' for s in j.get('steps', [])) for j in fallidos)


def ingesta_en_marcha():
    runs = gh_json('run', 'list', '--workflow', INGESTA, '--limit', '3', '--json', 'status')
    return any(r['status'] in ('in_progress', 'queued', 'waiting', 'pending') for r in runs)


def registro_fallo(run_id, lineas=250, run=None):
    if run is not None and 'registro' in run:   # publicación local: la cola de su publish.log y la traza
        return '\n'.join(l for l in run['registro'].splitlines() if l.strip())[-24000:]
    r = sh(['gh', 'run', 'view', str(run_id), '--log-failed', '--repo', GH_REPO], timeout=300)
    texto = re.sub(r'\x1b\[[0-9;]*m', '', r.stdout or r.stderr or '')
    # Fuera fechas y ruido de setup: lo que importa está al final.
    utiles = [re.sub(r'^\S+\t\S+\t\S+Z ', '', l) for l in texto.splitlines() if l.strip()]
    return '\n'.join(utiles[-lineas:])[-24000:]


def log(msg):
    ESTADO_DIR.mkdir(parents=True, exist_ok=True)
    linea = f"{dt.datetime.now().isoformat(timespec='seconds')} {msg}"
    print(linea, flush=True)
    with (ESTADO_DIR / 'autorepair.log').open('a', encoding='utf-8') as f:
        f.write(linea + '\n')


def cargar_estado():
    try:
        return json.loads((ESTADO_DIR / 'state.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def guardar_estado(estado):
    ESTADO_DIR.mkdir(parents=True, exist_ok=True)
    tmp = ESTADO_DIR / 'state.json.tmp'
    tmp.write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding='utf-8')
    tmp.replace(ESTADO_DIR / 'state.json')


def ident(texto) -> str:
    """Apto para nombre de rama y carpeta: los flujos locales llevan «:» y su id es una fecha ISO."""
    return re.sub(r'[^A-Za-z0-9._-]+', '-', str(texto)).strip('-')


def preparar_worktree(flujo, run_id):
    rama = f"autorepair/{ident(flujo.removesuffix('.yml'))}-{ident(run_id)}"
    wt = WT_BASE / f"wt-autorepair-{ident(run_id)}"
    sh(['git', 'fetch', '-q', 'origin', 'main'], check=True, timeout=300)
    quitar_worktree(wt)
    if wt.exists():   # algo la sigue teniendo abierta: otra ruta antes que perder la reparación
        wt = wt.with_name(f'{wt.name}-{int(time.time())}')
    sh(['git', 'branch', '-D', rama])
    sh(['git', 'worktree', 'add', '-q', '-b', rama, str(wt), 'origin/main'], check=True, timeout=600)
    nm = REPO / 'node_modules'
    if nm.is_dir() and not (wt / 'node_modules').exists():
        sh(['cmd', '/c', 'mklink', '/J', str(wt / 'node_modules'), str(nm)] if os.name == 'nt' else ['ln', '-s', str(nm), str(wt / 'node_modules')])
    return wt, rama


def quitar_worktree(wt):
    """Deja la ruta libre para `git worktree add`, quede como quede la pasada anterior.

    10/11: un `worktree remove` a medias (ficheros abiertos al cortar la pasada) dejó la carpeta con solo el enlace a
    node_modules y sin registro en git; `remove` ya no la reconocía y atlas falló cada hora con «already exists».
    """
    nm = wt / 'node_modules'
    if os.path.lexists(nm):
        # Primero el enlace, sin seguirlo: borrar su contenido sería borrar el node_modules del repo vivo.
        sh(['cmd', '/c', 'rmdir', str(nm)]) if os.name == 'nt' else nm.unlink()
    sh(['git', 'worktree', 'remove', '--force', str(wt)])
    sh(['git', 'worktree', 'prune'])
    if wt.exists() and not os.path.lexists(nm):
        shutil.rmtree(wt, ignore_errors=True)
    sh(['git', 'worktree', 'prune'])


def limpiar_worktree(wt):
    quitar_worktree(wt)


def deshacer(wt):
    sh(['git', 'checkout', '--', '.'], cwd=wt)
    sh(['git', 'clean', '-fdq', '-e', 'node_modules'], cwd=wt)


def pasos_fallidos(registro):
    """Los comandos que fallaron en el workflow, para que la puerta los repita sobre el arreglo.

    Reconoce el `CalledProcessError: Command '(python, scripts/x.py, …)'` de los scripts de carga y los
    `FAIL: test_x (test_modulo.Clase.test_x)` de unittest."""
    pasos = []
    for m in re.finditer(r"Command '\('[^']*python[^']*', ((?:'[^']*'(?:, )?)+)\)'", registro):
        args = re.findall(r"'([^']*)'", m.group(1))
        if args and re.fullmatch(r'scripts/[\w.-]+\.py', args[0]):
            pasos.append('python ' + ' '.join(args))
    for modulo in re.findall(r'^.*?(?:FAIL|ERROR): \w+ \((test_\w+)\.', registro, re.M):
        pasos.append(f'python -m unittest discover -s tests -p {modulo}.py')
    return list(dict.fromkeys(pasos))


def dejar_como_el_indice(wt):
    """Los pasos de la puerta construyen (`build-public-dist`, `build-reading-pinterest-rss --assign`) y escriben en el
    árbol. El arreglo del agente está en el índice (`git add -A` antes de la puerta): se vuelve a él, para que lo escrito
    por la puerta no acabe en el commit ni en el diff del siguiente agente."""
    sh(['git', 'checkout', '-q', '--', '.'], cwd=wt)
    sh(['git', 'clean', '-fdq', '--', '.', ':!node_modules'], cwd=wt)


def puerta_local(wt, registro=''):
    # Puerta por impacto (local-ci la elige sola) más los pasos que fallaron en el workflow. 10/11: la vía completa
    # rechazó tres arreglos correctos por falsos fallos del entorno y la carga pasó 4 h sin publicar.
    extra = [a for paso in pasos_fallidos(registro) for a in ('--tambien', paso)]
    r = sh([sys.executable, 'scripts/local-ci.py', '--baseline', *extra], cwd=wt, timeout=3 * 3600)
    dejar_como_el_indice(wt)
    salida = (r.stdout or '') + (r.stderr or '')
    guardar_puerta(wt, salida)
    return veredicto_puerta(r.returncode, salida, pasos_fallidos(registro))


def guardar_puerta(wt, salida, conservar=30):
    """La salida entera de cada puerta, con el detalle de cada fallo: el log solo lleva un resumen de 3000 caracteres.

    10/11: tres arreglos rechazados con 81–91 «ya fallaban en main» y nada que permitiera saber por qué."""
    carpeta = ESTADO_DIR / 'puertas'
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / f"{dt.datetime.now():%Y%m%dT%H%M%S}-{wt.name}.log").write_text(salida, encoding='utf-8')
    for viejo in sorted(carpeta.glob('*.log'))[:-conservar]:
        viejo.unlink(missing_ok=True)


def veredicto_puerta(codigo, salida, pasos=()):
    """Decide por el código de salida de local-ci, no por el texto: 0 pasa, 1 (fallos nuevos) no pasa.

    2 = algo agotó el tiempo y quedó sin verificar: pasa solo si no es uno de los pasos que fallaron en el workflow
    (esos tienen que verificarse aquí); el resto lo corre el CI obligatorio de GitHub antes del merge.
    """
    lentos = re.findall(r'sin verificar \(agotó [^)]*\): (.+)', salida)
    pasa = codigo == 0 or (codigo == 2 and not any(p in l or l in p for p in pasos for l in lentos))
    # Lo útil son las secciones «## comando» de cada fallo nuevo y el recuento final; la cola cruda las cortaba.
    fallos = re.findall(r'^## .*\n.*', salida, re.M)
    resumen = '\n'.join(fallos + [f'sin verificar: {l}' for l in lentos] + salida.strip().splitlines()[-1:])
    return pasa, resumen[-3000:]


def instantanea(flujo) -> str:
    """Estado real que el agente no puede consultar (va sin credenciales de gh): lo pone el turno de noche en el prompt.

    11/11: dos agentes «arreglaron» el reconocimiento de la propuesta del bot cuando lo que bloqueaba la carga era otra
    PR abierta (la de Amazon, con el mismo prefijo de rama). Con la lista de PR abiertas delante se veía a la primera."""
    partes = []
    try:
        prs = gh_json('pr', 'list', '--state', 'open', '--limit', '40', '--json', 'number,headRefName,author,createdAt,title')
        partes.append('PR abiertas (número, rama, autor, creada, título):\n' + ('\n'.join(
            f"#{p['number']} {p['headRefName']} {(p.get('author') or {}).get('login', '?')} {p['createdAt'][:16]} {p['title'][:90]}"
            for p in prs) or '(ninguna)'))
    except Exception as exc:
        partes.append(f'PR abiertas: no disponibles ({exc})')
    if not es_local(flujo):
        try:
            runs = gh_json('run', 'list', '--workflow', flujo, '--limit', '8',
                           '--json', 'createdAt,event,headBranch,headSha,status,conclusion')
            partes.append(f'Últimas ejecuciones de {flujo} (fecha, evento, rama, commit, resultado):\n' + '\n'.join(
                f"{r['createdAt'][:16]} {r['event']} {r['headBranch']} {r['headSha'][:10]} {r['conclusion'] or r['status']}"
                for r in runs))
        except Exception as exc:
            partes.append(f'Ejecuciones: no disponibles ({exc})')
    try:
        commits = sh(['git', 'log', '--format=%h %ad %s', '--date=format:%m-%d %H:%M', '-15', 'origin/main']).stdout.strip()
    except Exception:
        commits = ''
    partes.append('Últimos commits de main:\n' + (commits or '(no disponibles)'))
    return ("\n\n## Estado real ahora (lo consulta el turno de noche; tú no tienes gh)\n```\n"
            + '\n\n'.join(partes)[-8000:] + "\n```")


def reparar(flujo, run, dry, historial=None):
    registro = registro_fallo(run['databaseId'], run=run if es_local(flujo) else None)
    if dry:
        log(f"[dry] {flujo}: repararía con {[a[0] for a in agentes()]}; registro {len(registro)} caracteres; "
            f"{len(historial or [])} intentos anteriores")
        return None
    wt, rama = preparar_worktree(flujo, run['databaseId'])
    prompt = prompt_reparacion(flujo, run, registro, historial, instantanea(flujo))
    try:
        for nombre, argv, env, trailer in agentes():
            log(f"{flujo}: probando {nombre}")
            args = [exe(argv[0]), *argv[1:]] + (['-C', str(wt), '-'] if nombre == 'codex' else [])
            try:
                r = sh(args, cwd=wt, timeout=90 * 60, env={**sin_escritura(ESTADO_DIR / 'gh-sin-credenciales'), **env},
                       entrada=prompt)
                salida = (r.stdout or '') + (r.stderr or '')
            except subprocess.TimeoutExpired:
                log(f"{flujo}: {nombre} superó 90 min"); deshacer(wt); continue
            if sin_cuota(salida) and r.returncode:
                log(f"{flujo}: {nombre} sin cuota → siguiente"); deshacer(wt); continue
            if (wt / 'AUTOREPAIR_NOFIX.md').exists():
                motivo = (wt / 'AUTOREPAIR_NOFIX.md').read_text(encoding='utf-8', errors='replace')[:1500]
                log(f"{flujo}: {nombre} dice que no hay arreglo en código: {motivo[:300]!r}")
                return {'sin_arreglo': motivo, 'agente': nombre}
            resumen_f = wt / 'AUTOREPAIR_SUMMARY.md'
            resumen = resumen_f.read_text(encoding='utf-8', errors='replace').strip() if resumen_f.exists() else ''
            resumen_f.unlink(missing_ok=True)
            sh(['git', 'add', '-A', '--', '.', ':!node_modules'], cwd=wt)
            ok, motivo = diff_valido(sh(['git', 'diff', '--cached'], cwd=wt).stdout)
            if not ok:
                log(f"{flujo}: {nombre} rechazado ({motivo})"); sh(['git', 'reset', '-q'], cwd=wt); deshacer(wt); continue
            pasa, salida_puerta = puerta_local(wt, registro)
            if not pasa:
                # No se tira el arreglo: el siguiente agente parte de él y de lo que dijo la puerta (10/11: tres
                # arreglos correctos rehechos desde cero, uno tras otro).
                log(f"{flujo}: {nombre} no pasa la puerta local:\n{salida_puerta[-1500:]}"); sh(['git', 'reset', '-q'], cwd=wt)
                prompt = prompt_continuar(prompt, nombre, salida_puerta); continue
            titulo = (resumen.splitlines() or [f'Reparar {flujo}'])[0].lstrip('# ').strip()[:90] or f'Reparar {flujo}'
            cuerpo = '\n'.join(resumen.splitlines()[1:]).strip()
            mensaje = f"{titulo}\n\nReparación automática del turno de noche ({nombre}) tras dos fallos de {flujo}.\n{run['url']}\n\n{cuerpo}".strip()
            if trailer:
                mensaje += '\n\n' + trailer
            sh(['git', 'commit', '-q', '-F', '-'], cwd=wt, entrada=mensaje, check=True)
            sh(['git', 'push', '-q', '-u', 'origin', rama], cwd=wt, check=True, timeout=600)
            body = (f"## Qué falló\n`{flujo}` falló dos veces seguidas en main: {run['url']}\n\n## Arreglo ({nombre})\n{cuerpo or titulo}\n\n"
                    f"## Comprobado\n- Puerta local por impacto (`local-ci.py --baseline` + los pasos que fallaron): sin fallos nuevos.\n- Al entrar en main, el turno de noche relanza `{flujo}`.\n\n{PIE_PR}")
            url = sh(['gh', 'pr', 'create', '--repo', GH_REPO, '--base', 'main', '--head', rama, '--title', titulo, '--body-file', '-'],
                     cwd=wt, entrada=body, check=True).stdout.strip().splitlines()[-1]
            numero = int(url.rstrip('/').rsplit('/', 1)[-1])
            sh(['gh', 'pr', 'merge', str(numero), '--repo', GH_REPO, '--auto', '--squash'])
            log(f"{flujo}: PR {url} con auto-merge ({nombre})")
            return {'pr': numero, 'agente': nombre, 'titulo': titulo}
        log(f"{flujo}: ninguna IA dejó un arreglo válido")
        return {'fallido': True}
    finally:
        limpiar_worktree(wt)


def pasada(dry=False, solo=None):
    estado = cargar_estado()
    ahora = dt.datetime.now(dt.timezone.utc)
    hoy = ahora.date().isoformat()
    caida = actions_caido()
    if caida:
        log(f"GitHub Actions en incidencia ({caida}): no relanzo ni reparo nada; reintento en la siguiente pasada")
    if not solo or solo == INGESTA:
        try:
            if not caida and carga_perdida(ultima_ejecucion(INGESTA), ahora, estado.get('carga_perdida') == hoy):
                log(f"{'[dry] ' if dry else ''}{INGESTA}: hoy no se ha lanzado la carga nocturna; la lanzo")
                dry or sh(['gh', 'workflow', 'run', INGESTA, '--ref', 'main', '--repo', GH_REPO], check=True)
                estado['carga_perdida'] = hoy
        except Exception as exc:
            log(f"{INGESTA}: no pude comprobar si la carga se lanzó: {exc}")
    for flujo in [solo] if solo else [*VIGILADOS, *flujos_locales()]:
        try:
            run = ultima_ejecucion(flujo)
            previo = estado.get(flujo)
            if previo and previo.get('pr') and not previo.get('pr_cerrada'):
                pr = gh_json('pr', 'view', str(previo['pr']), '--json', 'state,createdAt,statusCheckRollup')
                if pr['state'] == 'MERGED':
                    log(f"{flujo}: PR #{previo['pr']} en main → relanzo el flujo")
                    dry or relanzar(flujo, run)
                    previo.update(pr_cerrada=True, relanzado=ahora.isoformat())
                    anotar(previo, 'mergeada; se relanza el flujo para comprobarla')
                    continue
                if pr['state'] == 'CLOSED':
                    previo['pr_cerrada'] = True
                    anotar(previo, 'PR cerrada sin entrar')
                elif (motivo := pr_atascada(pr, ahora)):
                    log(f"{flujo}: PR #{previo['pr']} no puede entrar ({motivo}); la cierro y cuento el intento como fallido")
                    dry or sh(['gh', 'pr', 'close', str(previo['pr']), '--repo', GH_REPO, '--delete-branch', '--comment',
                               f'Cerrada por el turno de noche: {motivo}. El siguiente intento parte de este historial.'])
                    previo['pr_cerrada'] = True
                    anotar(previo, motivo)
            intentos = sum(1 for x in (previo or {}).get('intentos', []) if x.startswith(hoy))
            fallido = run and run.get('status') == 'completed' and run.get('conclusion') in ('failure', 'timed_out', 'startup_failure')
            infra = bool(fallido) and not es_local(flujo) and fallo_de_infraestructura(run['databaseId'])
            accion = decidir(run, previo, ahora, intentos, infra)
            if caida and accion in ('relanzar', 'reparar'):
                continue
            if infra and accion == 'relanzar':
                log(f"{'[dry] ' if dry else ''}{flujo}: fallo de GitHub, no del código; relanzo {run['url']}")
                dry or relanzar(flujo, run)
                estado.setdefault(flujo, {})['relanzado'] = ahora.isoformat()
                continue
            if accion == 'nada':
                continue
            if accion == 'olvidar':
                log(f"{flujo}: verde de nuevo"); estado.pop(flujo, None); continue
            if accion == 'esperar_pr':
                continue
            if accion == 'agotado':
                if (previo or {}).get('avisado') != hoy:
                    log(f"{flujo}: {MAX_INTENTOS_DIA} reparaciones hoy sin éxito; aviso a David ({run['url']})")
                    e = estado.setdefault(flujo, {})
                    e['avisado'] = hoy
                    if not dry:
                        e['issue'] = avisar(flujo, run, e.get('historial'), e.get('issue'))
                continue
            if accion == 'relanzar':
                log(f"{'[dry] ' if dry else ''}{flujo}: primer fallo, relanzo {run['url']}")
                dry or relanzar(flujo, run)
                estado.setdefault(flujo, {})['relanzado'] = ahora.isoformat()
                continue
            if flujo != INGESTA and ingesta_en_marcha():
                log(f"{flujo}: la carga del catálogo está en marcha; reparo en la siguiente pasada"); continue
            res = reparar(flujo, run, dry, (previo or {}).get('historial'))
            if res is not None:
                registrar_intento(estado.setdefault(flujo, {}), res, run, ahora)
        except Exception as exc:   # un flujo roto no puede parar la vigilancia de los demás
            log(f"{flujo}: error del turno de noche: {exc}")
        finally:
            dry or guardar_estado(estado)


def registrar_intento(e: dict, res: dict, run: dict, ahora: dt.datetime):
    e.setdefault('intentos', []).append(ahora.isoformat())
    for k in ('sin_arreglo', 'fallido', 'pr', 'agente', 'titulo'):
        e.pop(k, None)
    e.update(res, run=run['databaseId'], pr_cerrada=not res.get('pr'))
    if res.get('pr'):
        resultado = 'PR abierta con auto-merge'
    elif res.get('sin_arreglo'):
        resultado = 'sin arreglo en código: ' + str(res['sin_arreglo'])[:200]
    else:
        resultado = 'ninguna IA dejó un arreglo que pasara la puerta local'
    e.setdefault('historial', []).append({'fecha': ahora.isoformat(), 'agente': res.get('agente', '-'), 'pr': res.get('pr'),
                                          'titulo': res.get('titulo', ''), 'run': run.get('url'), 'resultado': resultado})
    del e['historial'][:-HISTORIAL_MAX]


def anotar(previo: dict, resultado: str):
    """Completa el último intento del historial con lo que pasó después con su PR."""
    if previo.get('historial'):
        previo['historial'][-1]['resultado'] = resultado


def pr_atascada(pr: dict, ahora: dt.datetime) -> str:
    """Motivo para dar por perdida una PR de reparación abierta, o '' si aún puede entrar.

    Antes se esperaba sin límite: una PR con el CI rojo dejaba el flujo en «esperar_pr» para siempre, sin más intentos."""
    edad = ahora - dt.datetime.fromisoformat(pr['createdAt'].replace('Z', '+00:00'))
    checks = pr.get('statusCheckRollup') or []
    concl = lambda c: (c.get('conclusion') or c.get('state') or '').upper()
    pendientes = [c for c in checks if (c.get('status') or 'COMPLETED').upper() != 'COMPLETED'
                  or concl(c) in ('PENDING', 'EXPECTED', '')]
    rojos = sorted({c.get('name') or c.get('context') or '?' for c in checks
                    if concl(c) in ('FAILURE', 'ERROR', 'TIMED_OUT', 'STARTUP_FAILURE', 'ACTION_REQUIRED')})
    if rojos and not pendientes and edad > dt.timedelta(minutes=PR_BLOQUEADA_MIN):
        return 'CI rojo en la PR: ' + ', '.join(rojos)[:300]
    if edad > dt.timedelta(hours=PR_CADUCA_H):
        return f'CI rojo o atascado: {PR_CADUCA_H} h sin entrar' + (' (' + ', '.join(rojos)[:200] + ')' if rojos else '')
    return ''


def relanzar(flujo, run):
    """Workflow: dispatch nuevo sobre main. Local: el mismo comando con el código de main (el bucle solo actualiza su
    copia al arrancar, una vez al día: sin esto, un arreglo ya mergeado no se probaba hasta el día siguiente)."""
    if not es_local(flujo):
        sh(['gh', 'workflow', 'run', flujo, '--ref', 'main', '--repo', GH_REPO], check=True)
        return
    cwd = Path(run['cwd'])
    sh(['git', 'fetch', '-q', 'origin', 'main'], cwd=cwd, timeout=300)
    sh(['git', 'checkout', '-q', '--detach', 'origin/main'], cwd=cwd)
    with open(run['registro_ruta'], 'a', encoding='utf-8') as salida:
        salida.write(f"--- {dt.datetime.now():%Y-%m-%d %H:%M} relanzada por la autorreparación\n")
        salida.flush()
        banderas = (0x00000008 | 0x00000200) if os.name == 'nt' else 0   # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        subprocess.Popen(run['argv'], cwd=cwd, stdout=salida, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                         creationflags=banderas, start_new_session=os.name != 'nt')


def avisar(flujo, run, historial, issue=None):
    """Intentos agotados: issue en GitHub (visible y persistente) y aviso en el escritorio de este equipo.
    Antes solo se escribía «queda para David» en un log que nadie leía."""
    titulo = f'Autorreparación agotada: {flujo}'
    cuerpo = (f"{describir(flujo, run)} sigue fallando tras {MAX_INTENTOS_DIA} reparaciones automáticas hoy."
              f"{historial_texto(historial)}\n\nEstado y registros en este equipo: `%LOCALAPPDATA%/web-escritor-autorepair` "
              f"(autorepair.log, puertas/). El turno de noche lo vuelve a intentar mañana.\n\n{PIE_PR}")
    numero = issue
    try:
        if issue and gh_json('issue', 'view', str(issue), '--json', 'state')['state'] == 'OPEN':
            sh(['gh', 'issue', 'comment', str(issue), '--repo', GH_REPO, '--body-file', '-'], entrada=cuerpo, check=True)
        else:
            url = sh(['gh', 'issue', 'create', '--repo', GH_REPO, '--title', titulo, '--body-file', '-'],
                     entrada=cuerpo, check=True).stdout.strip().splitlines()[-1]
            numero = int(url.rstrip('/').rsplit('/', 1)[-1])
        log(f"{flujo}: aviso en la issue #{numero}")
    except Exception as exc:
        log(f"{flujo}: no pude abrir la issue de aviso: {exc}")
    aviso_escritorio(titulo, f'Issue #{numero}' if numero else 'Mira autorepair.log')
    return numero


def aviso_escritorio(titulo, texto):
    if os.name != 'nt':
        return
    limpio = lambda t: re.sub(r"[^\w .:#()/-]", '', t)
    ps = ("[Windows.UI.Notifications.ToastNotificationManager,Windows.UI.Notifications,ContentType=WindowsRuntime]|Out-Null;"
          "$x=[Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent("
          "[Windows.UI.Notifications.ToastTemplateType]::ToastText02);$t=$x.GetElementsByTagName('text');"
          f"$t.Item(0).InnerText='{limpio(titulo)}';$t.Item(1).InnerText='{limpio(texto)}';"
          "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Windows PowerShell')"
          ".Show([Windows.UI.Notifications.ToastNotification]::new($x))")
    try:
        sh(['powershell', '-NoProfile', '-Command', ps], timeout=60)
    except Exception:
        pass


def sin_escritura(vacio):
    """Entorno del agente sin credenciales de escritura: ni push ni gh autenticado.

    El agente solo edita el worktree; el push, la PR y el auto-merge los hace el orquestador tras la puerta local.
    Antes heredaba el gh y el git de la máquina y podía empujar o mergear saltándose la puerta.
    """
    vacio.mkdir(parents=True, exist_ok=True)
    return {'GH_CONFIG_DIR': str(vacio), 'GH_TOKEN': '', 'GITHUB_TOKEN': '', 'GH_ENTERPRISE_TOKEN': '',
            'GIT_TERMINAL_PROMPT': '0', 'GCM_INTERACTIVE': 'never',
            'GIT_CONFIG_COUNT': '2',
            'GIT_CONFIG_KEY_0': 'remote.origin.pushurl', 'GIT_CONFIG_VALUE_0': 'sin-push://lo-hace-el-orquestador',
            'GIT_CONFIG_KEY_1': 'credential.helper', 'GIT_CONFIG_VALUE_1': ''}


def tomar_cerrojo(ruta):
    """Cerrojo del sistema sobre el fichero: lo suelta el sistema al morir el proceso, sin caducidad.

    Antes valía la antigüedad del fichero (6 h): una pasada viva más de 6 h dejaba entrar otra a la vez, y una que
    moría sin borrar el fichero bloqueaba las siguientes hasta que caducaba. Devuelve el fichero abierto (cerrarlo lo
    suelta) o None si otro proceso lo tiene.
    """
    f = open(ruta, 'a+')
    try:
        if os.name == 'nt':
            import msvcrt
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        f.close()
        return None
    f.seek(0)
    f.truncate()
    f.write(str(os.getpid()))
    f.flush()
    return f


def main():
    # La tarea redirige la salida a salida.log con la página de códigos de Windows: un «→» tumbaba la pasada
    # ('charmap' codec, 2026-11-09/10, en cada intento con Telegram).
    for flujo in (sys.stdout, sys.stderr):
        flujo.reconfigure(encoding='utf-8', errors='replace')
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--solo')
    a = ap.parse_args()
    ESTADO_DIR.mkdir(parents=True, exist_ok=True)
    cerrojo = tomar_cerrojo(ESTADO_DIR / 'lock')
    if cerrojo is None:
        print('Otra pasada sigue en marcha'); return 0
    try:
        pasada(a.dry_run, a.solo)
    finally:
        cerrojo.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
