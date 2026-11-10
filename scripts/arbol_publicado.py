"""El árbol publicado: lo versionado más lo generado que hay en disco (fase 5 de docs/arquitectura-catalogo).

Hasta ahora los checks enumeraban páginas con `git ls-files '*.html'`. Cuando lo generado (fichas, editoriales,
Pagefind, sitemap…) deje de versionarse, ese listado lo perdería en silencio: unas 6800 páginas sin comprobar ni
publicar. Este módulo da el mismo listado que `git ls-files` más lo generado materializado en disco.

Para no reescribir cada llamada, `run` y `check_output` imitan a `subprocess` (mismo tipo, mismo formato, mismos
errores) cuando la orden es `git [-c core.quotepath=…] ls-files [-z] [--] [patrones]`. Cualquier otra orden de git se
ejecuta tal cual. Un trinquete (tests/test_arbol_publicado.py) impide volver a llamar a `git ls-files` a pelo.

    import arbol_publicado
    arbol_publicado.run(['git', 'ls-files', '-z', '*.html'], cwd=ROOT, capture_output=True, text=True)
    arbol_publicado.listar(ROOT, '*.html')          # lista de rutas relativas, ordenada y sin repetidos
    python scripts/arbol_publicado.py -z '*.html'   # CLI (la usan los .mjs): misma salida que git ls-files
"""
from __future__ import annotations

import fnmatch
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from materializar_generados import GENERADOS, TESTIGO  # noqa: E402  (una sola lista de lo generado)


def _coincide(ruta: str, patron: str) -> bool:
    """Pathspec de git sin magia: igual, carpeta que lo contiene o comodín (el `*` cruza `/`)."""
    patron = patron[2:] if patron.startswith('./') else patron
    if not patron or patron == '.':
        return True
    if ruta == patron or ruta.startswith(patron.rstrip('/') + '/'):
        return True
    return fnmatch.fnmatchcase(ruta, patron)


def generados_en_disco(root: Path) -> set[str]:
    """Lo generado que existe en disco, versionado o no (tras el corte, solo lo materializa el builder)."""
    root = Path(root)
    encontrados: set[str] = set()
    for patron in GENERADOS:
        base = patron.split('*', 1)[0].rsplit('/', 1)[0] if '/' in patron.split('*', 1)[0] else ''
        if '*' not in patron:
            if (root / patron).is_file():
                encontrados.add(patron)
            continue
        if not base:   # en la raíz (sitemap*.xml): sin recorrer el repo entero
            nombres = (e.name for e in os.scandir(root) if e.is_file())
            encontrados.update(n for n in nombres if fnmatch.fnmatchcase(n, patron))
            continue
        carpeta = root / base
        if not carpeta.is_dir():
            continue
        for dirpath, _dirs, files in os.walk(carpeta):
            rel_dir = Path(dirpath).relative_to(root).as_posix()
            for nombre in files:
                rel = f'{rel_dir}/{nombre}'
                if fnmatch.fnmatchcase(rel, patron):
                    encontrados.add(rel)
    return encontrados


def _materializar_si_falta(root: Path) -> None:
    """Tras el corte, un job que no materializó vería el sitio sin fichas y pasaría en vacío: materializa aquí.

    Antes del corte (testigo versionado) o con lo generado ya en disco no hace nada. La salida del builder va a
    stderr para no mezclarse con el listado (la CLI imita a `git ls-files`).
    """
    if (root / TESTIGO).exists():
        return
    versionado = subprocess.run(['git', 'ls-files', '--', TESTIGO], cwd=root, capture_output=True)
    if versionado.returncode != 0 or versionado.stdout.strip():
        return
    script = root / 'scripts' / 'materializar_generados.py'
    if not script.exists():
        return   # otro repo (tests con repos temporales): no hay builder que llamar
    resumen = os.environ.get('GITHUB_STEP_SUMMARY')
    if resumen:   # en CI es correcto pero lento: el job debería usar .github/actions/materializar (con caché)
        with open(resumen, 'a', encoding='utf-8', newline='\n') as f:
            f.write(f'> ⚠️ `{os.environ.get("GITHUB_WORKFLOW", "?")}` / `{os.environ.get("GITHUB_JOB", "?")}`: '
                    'lista el árbol sin haber materializado; añade `./.github/actions/materializar` al job.\n')
    subprocess.run([sys.executable, str(script), '--asegurar'], cwd=root, stdout=sys.stderr, check=True)
    if not (root / TESTIGO).exists():
        raise RuntimeError(f'materializar_generados.py --asegurar no dejó {TESTIGO}: el árbol publicado estaría incompleto')


def listar(root: Path, *patrones: str) -> list[str]:
    """`git ls-files -- patrones` ∪ lo generado en disco que casa con ellos. Ordenado como git, sin repetidos."""
    _materializar_si_falta(Path(root))
    salida = subprocess.run(['git', 'ls-files', '-z', '--', *patrones], cwd=root, capture_output=True, check=True)
    versionado = {p for p in salida.stdout.decode('utf-8').split('\0') if p}
    extra = {p for p in generados_en_disco(root) if not patrones or any(_coincide(p, x) for x in patrones)}
    return sorted(versionado | extra, key=lambda p: p.encode('utf-8'))


def _entender(args) -> tuple[list[str], bool, list[str]] | None:
    """(-c de git, -z, patrones) si es un `git ls-files` que sabemos imitar; si no, None."""
    args = [str(a) for a in args]
    if not args or Path(args[0]).stem != 'git':
        return None
    i, config = 1, []
    while i + 1 < len(args) and args[i] == '-c':
        config += args[i:i + 2]
        i += 2
    if i >= len(args) or args[i] != 'ls-files':
        return None
    z, patrones, fin = False, [], False
    for a in args[i + 1:]:
        if not fin and a == '-z':
            z = True
        elif not fin and a == '--':
            fin = True
        elif not fin and a.startswith('-'):
            return None   # --others, -u, --stage…: otra pregunta; la contesta git tal cual
        else:
            patrones.append(a)
    return config, z, patrones


def _cita(ruta: str) -> str:
    """Como git con core.quotepath=true: rutas no ASCII entre comillas y en octal."""
    if ruta.isascii() and not any(c in ruta for c in '"\\\t\n'):
        return ruta
    trozos = []
    for b in ruta.encode('utf-8'):
        c = chr(b)
        trozos.append({'"': '\\"', '\\': '\\\\', '\t': '\\t', '\n': '\\n'}.get(c, c) if b < 0x80 else f'\\{b:03o}')
    return '"' + ''.join(trozos) + '"'


def _formatear(rutas: list[str], z: bool, config: list[str]) -> bytes:
    if z:
        return b''.join(r.encode('utf-8') + b'\0' for r in rutas)
    sin_citar = any(c.replace(' ', '').lower() in ('core.quotepath=false', 'core.quotepath=off', 'core.quotepath=0')
                    for c in config[1::2])
    return b''.join(((r if sin_citar else _cita(r)) + '\n').encode('utf-8') for r in rutas)


def _salida(args, kwargs) -> bytes | None:
    entendido = _entender(args)
    if entendido is None:
        return None
    config, z, patrones = entendido
    root = kwargs.get('cwd') or os.getcwd()
    try:
        rutas = listar(Path(root), *patrones)
    except (OSError, subprocess.CalledProcessError):
        return None   # que falle git de verdad, con su error de siempre
    return _formatear(rutas, z, config)


def _texto(kwargs) -> str | None:
    if kwargs.get('text') or kwargs.get('universal_newlines') or kwargs.get('encoding') or kwargs.get('errors'):
        return kwargs.get('encoding') or 'utf-8'
    return None


def run(args, **kwargs):
    """`subprocess.run` que, para `git ls-files`, devuelve el árbol publicado."""
    capturar = kwargs.get('capture_output') or kwargs.get('stdout') == subprocess.PIPE
    datos = _salida(args, kwargs) if capturar else None
    if datos is None:
        return subprocess.run(args, **kwargs)
    cod = _texto(kwargs)
    stdout = datos.decode(cod, kwargs.get('errors') or 'strict') if cod else datos
    return subprocess.CompletedProcess(args, 0, stdout, '' if cod else b'')


def check_output(args, **kwargs):
    """`subprocess.check_output` que, para `git ls-files`, devuelve el árbol publicado."""
    datos = _salida(args, kwargs)
    if datos is None:
        return subprocess.check_output(args, **kwargs)
    cod = _texto(kwargs)
    return datos.decode(cod, kwargs.get('errors') or 'strict') if cod else datos


def main(argv: list[str]) -> int:
    datos = _salida(['git', 'ls-files', *argv], {'cwd': os.getcwd()})
    if datos is None:
        return subprocess.run(['git', 'ls-files', *argv]).returncode
    sys.stdout.buffer.write(datos)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
