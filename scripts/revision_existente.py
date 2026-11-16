#!/usr/bin/env python3
"""Revisión rotativa del código que YA está en main, no solo de los cambios nuevos (David, 14/11/2026).

Cada día toma un grupo de ficheros y abre una PR que nunca se fusiona: su base es main sin esos ficheros y su cabeza
es main, así que el diff es el fichero entero y los revisores gratuitos (Codex, CodeRabbit) lo leen completo. Los
commits llevan la marca de no-CI y el push con GITHUB_TOKEN no dispara workflows: no gasta la cola de Actions.
Las PR y ramas de revisión se cierran solas a los pocos días.

Gemini Code Assist gratuito dejó de revisar el 17/07/2026 y Jules pasó a solo lectura el 11/11/2026 (cierra el
31/12): no se usan (#1314, CodeRabbit).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import git_estado  # noqa: E402
import gh_listas  # noqa: E402
PREFIX = 'revision/'
MAX_LINEAS = 1800
SKIP = '[skip ci]'
# Primero la tubería nocturna (de donde salen los fallos de cada mañana); después el resto en paquetes.
FIJOS = [
    ('publicacion-carga', ['scripts/refresh-reading-catalogue.py', 'scripts/publish-reading-refresh.py',
                           'scripts/publish-radar-refresh.py', 'scripts/merge-main.py', 'scripts/git_estado.py',
                           'scripts/materializar_generados.py', 'scripts/ci_intake_backup.py']),
    ('ingesta', ['scripts/reading_intake_pipeline.py', 'scripts/reading_intake_fetch.py', 'scripts/catalogo_estado.py',
                 'scripts/reading_quarantine.py', 'scripts/import-reading-sheet.py']),
    ('amazon', ['scripts/catalogo_amazon.py']),
    ('construccion-catalogo', ['scripts/build-reading-catalogue.py', 'scripts/check-reading-data.py']),
    ('workflows-carga', ['.github/workflows/reading-catalogue-sync.yml']),
]
EXT = ('.py', '.mjs', '.js', '.sh', '.yml', '.yaml')


def git(*args, env=None):
    return subprocess.run(['git', *args], cwd=ROOT, check=True, capture_output=True, text=True,
                          env={**os.environ, **(env or {})}).stdout.strip()


def gh(*args):
    return subprocess.run(['gh', *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def lineas(path):
    try:
        with (ROOT / path).open(encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def grupos():
    """Grupos fijos y, después, el resto de scripts/ y workflows en paquetes de <= MAX_LINEAS, los que más cambian
    antes (los fallos salen de lo que se toca). Determinista para un mismo árbol."""
    vistos = {f for _, fs in FIJOS for f in fs}
    salida = [(n, [f for f in fs if (ROOT / f).exists()]) for n, fs in FIJOS]
    rastreados = [p for p in git('ls-files', '-z', '--', 'scripts', '.github/workflows').split('\0')
                  if p and p.endswith(EXT) and p not in vistos and '/templates/' not in p]
    cambios = {}
    for linea in git('log', '--since=90.days', '--name-only', '--format=', '--', 'scripts', '.github/workflows').splitlines():
        cambios[linea] = cambios.get(linea, 0) + 1
    rastreados.sort(key=lambda p: (-cambios.get(p, 0), p))
    paquete, total = [], 0
    for p in rastreados:
        n = lineas(p)
        if paquete and total + n > MAX_LINEAS:
            salida.append(('paquete-%02d' % (len(salida) - len(FIJOS) + 1), paquete))
            paquete, total = [], 0
        paquete.append(p)
        total += n
    if paquete:
        salida.append(('paquete-%02d' % (len(salida) - len(FIJOS) + 1), paquete))
    return [(n, fs) for n, fs in salida if fs]


def elegir(nombre=None, hoy=None):
    todos = grupos()
    if nombre:
        for g in todos:
            if g[0] == nombre:
                return g
        raise SystemExit('Grupo desconocido: %s. Hay: %s' % (nombre, ', '.join(n for n, _ in todos)))
    hoy = hoy or datetime.now(ZoneInfo('Europe/Madrid')).date()
    return todos[(hoy - date(2026, 11, 14)).days % len(todos)]


CUERPO = """Revisión del código **existente** (no de un cambio): el diff muestra los ficheros enteros tal como están en main.
**No fusionar.** Se cierra sola en unos días.

Grupo `{nombre}`:
{lista}

Qué buscar (ver AGENTS.md, «Review guidelines»):
- Un libro, fila o fichero malo que tumba un lote entero en vez de quedar en cuarentena con su id.
- Salida de git o de herramientas leída por texto o por cortes de columna (`[3:]`, `splitlines` sin `-z`).
- Datos de un checkpoint o de una carga que se pueden perder si falla un paso intermedio.
- Fechas u horas sin zona de Madrid; ventanas nocturnas mal calculadas.
- Reintentos sin límite, o errores tragados que dejan el estado a medias sin avisar.
- Reglas de CI que fallan sin nombrar el libro o la ruta culpable.

Indica cada fallo con un escenario concreto (entrada → resultado incorrecto). No hace falta comentar estilo.
"""

DISPAROS = ('@codex review', '@coderabbitai full review')


ESPEJO = '_revision/'


def arboles(main, ficheros, nombre):
    """Commits base y cabeza de la PR de revisión sobre `main`, sin tocar el checkout (índice aparte).

    - Solo cuentan los ficheros que existen en `main`: el grupo sale del checkout local, que puede ir por detrás o
      por delante (#1314, CodeRabbit); `rm --cached -f --ignore-unmatch` tampoco falla si alguno falta.
    - El GITHUB_TOKEN no puede empujar commits que cambien `.github/workflows/*` (falta el permiso `workflows`): esos
      ficheros se quedan en la base y la cabeza los añade como copia en `_revision/<ruta>`, que se lee igual."""
    ficheros = git_estado.en_commit(ROOT, main, ficheros)
    if not ficheros:
        raise SystemExit('Ningún fichero del grupo %s está en main' % nombre)
    flujos = [f for f in ficheros if f.startswith('.github/workflows/')]
    resto = [f for f in ficheros if f not in flujos]
    tmp = tempfile.mkdtemp()
    try:
        env = {'GIT_INDEX_FILE': os.path.join(tmp, 'index')}
        git('read-tree', main, env=env)
        if resto:
            git_estado.quitar_del_indice(ROOT, resto, env=env)
        base_arbol = git('write-tree', env=env)
        git('read-tree', main, env=env)
        for f in flujos:
            _, _, blob = git('ls-tree', main, '--', f).split('\t', 1)[0].split()
            git('update-index', '--add', '--cacheinfo', '100644,%s,%s' % (blob, ESPEJO + f), env=env)
        cabeza_arbol = git('write-tree', env=env)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    base_commit = git('commit-tree', base_arbol, '-p', main, '-m', 'Revisión %s: base sin el grupo %s' % (nombre, SKIP))
    cabeza_commit = git('commit-tree', cabeza_arbol, '-p', base_commit,
                        '-m', 'Revisión %s: ficheros completos %s' % (nombre, SKIP))
    return base_commit, cabeza_commit


def abrir(nombre=None, publicar=False):
    nombre, ficheros = elegir(nombre)
    dia = datetime.now(ZoneInfo('Europe/Madrid')).date().isoformat()
    lista = '\n'.join('- `%s`' % f + (' (copia en `%s%s`)' % (ESPEJO, f) if f.startswith('.github/workflows/') else '')
                      for f in ficheros)
    print('Grupo %s (%d ficheros, %d líneas)' % (nombre, len(ficheros), sum(lineas(f) for f in ficheros)))
    if not publicar:
        print(lista)
        return
    base, cabeza = PREFIX + 'base-%s-%s' % (nombre, dia), PREFIX + '%s-%s' % (nombre, dia)
    # Reintento del mismo día: la PR ya existe y `gh pr create` la rechazaría sin completar los disparos que faltan.
    # Se reutiliza sin mover sus ramas (#1314, CodeRabbit).
    abierta = gh_listas.lista(gh, 'pr', 'list', '--head', cabeza, '--state', 'open', '--json', 'url,comments', tope=10)
    if abierta:
        url, hechos = abierta[0]['url'], {c['body'].strip() for c in abierta[0]['comments']}
    else:
        git('fetch', '-q', 'origin', 'main')
        base_commit, cabeza_commit = arboles(git('rev-parse', 'origin/main'), ficheros, nombre)
        git('push', '-q', '--force', 'origin', '%s:refs/heads/%s' % (base_commit, base),
            '%s:refs/heads/%s' % (cabeza_commit, cabeza))
        url, hechos = gh('pr', 'create', '--base', base, '--head', cabeza, '--title',
                         'Revisión del código existente: ' + nombre,
                         '--body', CUERPO.format(nombre=nombre, lista=lista)), set()
    numero = url.rstrip('/').rsplit('/', 1)[-1]
    for disparo in DISPAROS:
        if disparo not in hechos:
            gh('pr', 'comment', numero, '--body', disparo)
    print('PR', url)


def cerrar(dias=3, publicar=False):
    """Cierra las PR de revisión con más de `dias` y borra sus dos ramas; las sueltas sin PR también."""
    limite = datetime.now(timezone.utc) - timedelta(days=dias)
    # Solo las abiertas: son las únicas que se cierran o protegen ramas; con `all` el histórico llenaba el tope.
    prs = gh_listas.lista(gh, 'pr', 'list', '--state', 'open', '--search', 'head:' + PREFIX,
                          '--json', 'number,state,createdAt,headRefName,baseRefName')
    vivas = set()
    for pr in prs:
        if not pr['headRefName'].startswith(PREFIX):
            continue
        creada = datetime.fromisoformat(pr['createdAt'].replace('Z', '+00:00'))
        if pr['state'] == 'OPEN' and creada > limite:
            vivas |= {pr['headRefName'], pr['baseRefName']}
            continue
        if pr['state'] == 'OPEN':
            print('Cierro PR #%s' % pr['number'])
            if publicar:
                gh('pr', 'close', str(pr['number']), '--comment', 'Revisión terminada: se cierra sin fusionar.')
    remotas = [r.split('refs/heads/', 1)[1] for r in  git('ls-remote', '--heads', 'origin', 'refs/heads/' + PREFIX + '*').split('\n') if r]
    for rama in remotas:
        fecha = re.search(r'(\d{4}-\d{2}-\d{2})$', rama)
        if rama in vivas or (fecha and date.fromisoformat(fecha.group(1)) > limite.date()):
            continue
        print('Borro rama', rama)
        if publicar:
            git('push', '-q', 'origin', '--delete', rama)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='orden', required=True)
    a = sub.add_parser('abrir')
    a.add_argument('--grupo')
    a.add_argument('--publicar', action='store_true')
    c = sub.add_parser('cerrar')
    c.add_argument('--dias', type=int, default=3)
    c.add_argument('--publicar', action='store_true')
    l = sub.add_parser('grupos')
    args = parser.parse_args()
    if args.orden == 'abrir':
        abrir(args.grupo, args.publicar)
    elif args.orden == 'cerrar':
        cerrar(args.dias, args.publicar)
    else:
        for n, fs in grupos():
            print('%-24s %5d  %s' % (n, sum(lineas(f) for f in fs), ' '.join(fs)[:150]))
