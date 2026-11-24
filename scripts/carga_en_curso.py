#!/usr/bin/env python3
"""¿Hay una carga de libros en curso? Consultarlo ANTES de fusionar cualquier PR.

Cada avance de main mientras la PR de datos está en CI repite su ciclo (~75 min) y la ingesta sale con código 75.
23/11: #1535 y #1537 se fusionaron durante la carga y fueron tres cargas seguidas sin entrar un libro. Fusionar
con una carga activa casi nunca compensa: se encola hasta que acabe. Desde el 24/11 lo hace cumplir el check de PR
«Main congelado por carga» (.github/workflows/congelar-main.yml, scripts/congelar_main.py), que espera en la PR.

    python scripts/carga_en_curso.py     # código 0 = libre, 1 = carga en curso (dice por qué), 2 = no se pudo mirar
"""
import json
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))  # módulos hermanos también al cargarlo con importlib
import gh_listas  # noqa: E402

WORKFLOW = 'reading-catalogue-sync.yml'
PREFIJO = 'automation/reading-catalogue-'
TEXTOS = 'automation/reading-catalogue-textos-'  # la PR de textos propios es de otro flujo, no es una carga


def gh(*args):
    return subprocess.run(['gh', *args], capture_output=True, text=True, encoding='utf-8', check=True, timeout=120).stdout


def motivos(ejecuciones, prs):
    """Por qué hay carga: ejecuciones sin terminar del workflow y PR de datos abiertas del bot."""
    razones = [f"ejecución {e['databaseId']} {e['status']} (desde {e['createdAt']})"
               for e in ejecuciones if e.get('status') != 'completed']
    razones += [f"PR #{p['number']} de datos abierta ({p['headRefName']})" for p in prs
                if p['headRefName'].startswith(PREFIJO) and not p['headRefName'].startswith(TEXTOS)]
    return razones


def main():
    try:
        ejecuciones = gh_listas.ultimas(gh, 'run', 'list', '-w', WORKFLOW, '--json', 'databaseId,status,createdAt', n=10)
        prs = gh_listas.lista(gh, 'pr', 'list', '--state', 'open', '--json', 'number,headRefName', tope=1000)
    except (subprocess.SubprocessError, OSError, ValueError, gh_listas.Truncada) as exc:
        print(f'No se pudo mirar la carga ({type(exc).__name__}): tratarla como en curso.', file=sys.stderr)
        return 2
    razones = motivos(ejecuciones, prs)
    for r in razones:
        print('Carga en curso: ' + r)
    if razones:
        print('No fusionar otras PR hasta que acabe: cada avance de main repite la CI de la carga.')
    return 1 if razones else 0


if __name__ == '__main__':
    raise SystemExit(main())
