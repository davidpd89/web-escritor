#!/usr/bin/env python3
"""Política del portero (R4-8, .ci/fable-direccion-2026-11-18.md §2.2): ¿se fusiona sola una PR del reparador?

Es la frontera de verdad: un parche que pasa la CI se ejecuta la noche siguiente con todos los secretos de la carga.
Por eso la fusión automática exige que el parche sea de una forma inofensiva, y lo demás se queda para David
(etiqueta `necesita-david`). La lista es de formas, no de nombres de fichero:

- no toca rutas protegidas (`.github/`, `AGENTS.md`, `CLAUDE.md`, `.claude/`, dependencias, esta política);
- solo toca ficheros cuyo contenido se puede revisar sin ejecutarlo: Python (por AST) y texto o datos;
- no añade, visto por AST, subprocesos, lectura del entorno, red, `eval`/`exec`/`compile`/`__import__` ni
  importaciones dinámicas;
- no supera el tope de líneas cambiadas.

Uso: python scripts/reparador_politica.py BASE HEAD  → sale con 0 si se puede fusionar sola; si no, imprime los
motivos (uno por línea) y sale con 1. La política no ejecuta nada del parche: solo lee blobs con `git show`.
"""
import ast
import subprocess
import sys
from collections import Counter
from pathlib import PurePosixPath

# Tope provisional: Fable no lo ha fijado (r4 §2.4 lo cita sin número). Un arreglo de una clase de fallo con su test
# cabe holgado; algo más grande merece que lo mire una persona.
MAX_LINEAS = 200

PROTEGIDAS_PREFIJO = ('.github/', '.claude/', '.husky/', '.devcontainer/')
PROTEGIDAS_NOMBRE = {
    'AGENTS.md', 'CLAUDE.md', 'package.json', 'package-lock.json', 'npm-shrinkwrap.json', '.npmrc',
    'pyproject.toml', 'setup.py', 'setup.cfg', 'Pipfile', 'Pipfile.lock', 'poetry.lock', '.pre-commit-config.yaml',
    '.coderabbit.yaml', 'CODEOWNERS',
}
PROPIA = {'scripts/reparador_politica.py', 'tests/test-reparador-politica.py'}
# Contenido que se revisa sin ejecutarlo. Lo demás (js, sh, yml, html con <script>…) va a David.
TEXTO = {'.md', '.txt', '.json', '.csv'}

# Nombres cuyo uso nuevo abre una vía de ejecución, de red o de lectura de secretos.
MODULOS = {'subprocess', 'socket', 'urllib', 'http', 'requests', 'httpx', 'aiohttp', 'ftplib', 'smtplib',
           'telnetlib', 'ctypes', 'importlib', 'pty', 'multiprocessing', 'webbrowser', 'pickle', 'marshal', 'shutil'}
BUILTINS = {'eval', 'exec', 'compile', '__import__', 'breakpoint'}
ATRIBUTOS_OS = {'system', 'popen', 'environ', 'getenv', 'putenv', 'environb', 'getenvb', 'execv', 'execve',
                'execvp', 'execl', 'execlp', 'spawnl', 'spawnv', 'spawnve', 'fork', 'startfile', 'posix_spawn'}


def protegida(path):
    p = PurePosixPath(path)
    return (path.startswith(PROTEGIDAS_PREFIJO) or p.name in PROTEGIDAS_NOMBRE or path in PROPIA
            or p.name.startswith('requirements') and p.suffix == '.txt')


def usos(source):
    """Cuenta los usos peligrosos de un módulo Python; None si no se puede analizar."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return None
    found = Counter()
    # `import os as o` y luego `o.environ`: los alias de os cuentan como os.
    alias_os = {'os'} | {a.asname for n in ast.walk(tree) if isinstance(n, ast.Import)
                         for a in n.names if a.name == 'os' and a.asname}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split('.')[0]
                if root in MODULOS:
                    found[f'import {root}'] += 1
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or '').split('.')[0]
            if root in MODULOS:
                found[f'import {root}'] += 1
            if root == 'os':
                for alias in node.names:
                    if alias.name in ATRIBUTOS_OS:
                        found[f'os.{alias.name}'] += 1
        elif isinstance(node, ast.Name) and node.id in BUILTINS:
            found[node.id] += 1
        elif isinstance(node, ast.Attribute):
            if node.attr in ATRIBUTOS_OS and isinstance(node.value, ast.Name) and node.value.id in alias_os:
                found[f'os.{node.attr}'] += 1
            elif node.attr in BUILTINS | {'getattr'} and isinstance(node.value, ast.Name) and node.value.id in {
                    'builtins', '__builtins__'}:
                found[f'builtins.{node.attr}'] += 1
            elif node.attr == 'modules' and isinstance(node.value, ast.Name) and node.value.id == 'sys':
                found['sys.modules'] += 1
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'getattr':
            # getattr(obj, nombre_variable) esquiva el análisis por nombre: solo vale con una cadena literal.
            if len(node.args) < 2 or not isinstance(node.args[1], ast.Constant):
                found['getattr dinámico'] += 1
    return +found


def revisar(cambios, lineas):
    """`cambios`: {ruta: (contenido_antes | None, contenido_después | None)}. `lineas`: líneas añadidas + quitadas.

    Devuelve los motivos por los que NO se fusiona sola; lista vacía ⇒ se puede fusionar.
    """
    motivos = []
    if lineas > MAX_LINEAS:
        motivos.append(f'el parche cambia {lineas} líneas (tope {MAX_LINEAS})')
    for path in sorted(cambios):
        antes, despues = cambios[path]
        if protegida(path):
            motivos.append(f'{path}: ruta protegida')
            continue
        suffix = PurePosixPath(path).suffix.lower()
        if suffix in TEXTO:
            continue
        if suffix != '.py':
            motivos.append(f'{path}: tipo {suffix or "sin extensión"} no revisable sin ejecutarlo')
            continue
        if despues is None:
            continue  # borrar un módulo no añade capacidades; la CI dice si algo lo usaba
        nuevos = usos(despues)
        if nuevos is None:
            motivos.append(f'{path}: no se puede analizar')
            continue
        viejos = (usos(antes) if antes is not None else None) or Counter()
        añadidos = nuevos - viejos
        if añadidos:
            motivos.append(f'{path}: añade {", ".join(sorted(añadidos))}')
    return motivos


def git(*args):
    return subprocess.run(['git', *args], capture_output=True, text=True, encoding='utf-8', errors='replace',
                          check=True).stdout


def blob(rev, path):
    try:
        return git('show', f'{rev}:{path}')
    except subprocess.CalledProcessError:
        return None


def main(base, head):
    lineas = 0
    cambios = {}
    # -z: rutas sin comillas ni escapes; --no-renames: un renombrado son dos rutas, las dos revisadas.
    campos = git('diff', '--numstat', '-z', '--no-renames', f'{base}...{head}').split('\0')
    for entrada in filter(None, campos):
        added, removed, path = entrada.split('\t', 2)
        if added == '-':
            cambios[path] = (None, None)
            lineas += MAX_LINEAS + 1  # binario: nunca se fusiona solo
            continue
        lineas += int(added) + int(removed)
        cambios[path] = (blob(base, path), blob(head, path))
    motivos = revisar(cambios, lineas)
    for motivo in motivos:
        print(motivo)
    return 1 if motivos else 0


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit('uso: reparador_politica.py BASE HEAD')
    sys.exit(main(*sys.argv[1:]))
