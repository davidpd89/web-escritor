#!/usr/bin/env python3
"""Inserta la acción materializar en cada workflow que lee lo generado (rearquitectura, paso 2/4).

Un workflow lee lo generado si sirve el árbol (`http.server`) o construye la distribución pública
(`build-public-dist.py`). En cada job que lo hace, el paso se inserta justo antes del primer paso que lo lee
(tras checkout, Python y dependencias). Es idempotente: un job que ya tiene la acción no se toca. `--check` falla si queda alguno sin ella.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCION = './.github/actions/materializar'
LEE_GENERADOS = re.compile(r'http\.server|build-public-dist\.py(?! --check-assetsignore)')
PASO = '{i}- name: Materializar generados\n{cond}{i}  uses: {accion}\n\n'


def _jobs(lineas: list[str]) -> list[tuple[int, int]]:
    """Rangos [inicio, fin) de cada job bajo `jobs:` (claves con 2 espacios de sangría)."""
    try:
        inicio = next(i for i, l in enumerate(lineas) if l.rstrip() == 'jobs:')
    except StopIteration:
        return []
    cabeceras = [i for i in range(inicio + 1, len(lineas)) if re.match(r'^  [A-Za-z0-9_-]+:\s*$', lineas[i])]
    fin_jobs = next((i for i in range(inicio + 1, len(lineas)) if re.match(r'^\S', lineas[i])), len(lineas))
    return [(c, (cabeceras[k + 1] if k + 1 < len(cabeceras) else fin_jobs)) for k, c in enumerate(cabeceras)]


def adoptar(texto: str) -> str:
    lineas = texto.splitlines(keepends=True)
    for inicio, fin in reversed(_jobs(lineas)):
        cuerpo = ''.join(lineas[inicio:fin])
        if not LEE_GENERADOS.search(cuerpo) or ACCION in cuerpo:
            continue
        primera = next(i for i in range(inicio, fin) if LEE_GENERADOS.search(lineas[i]))
        paso = primera
        while paso > inicio and not re.match(r'^\s*- ', lineas[paso]):
            paso -= 1
        if paso == inicio:
            continue
        i = re.match(r'^(\s*)', lineas[paso]).group(1)
        # Si el paso que lee lo generado es condicional, la acción hereda la condición (no materializa en vano).
        cond = ''
        for j in range(paso, fin):
            if j > paso and re.match(rf'^{i}- ', lineas[j]):
                break
            m = re.match(rf'^{i}(?:- |  )if:(.*)$', lineas[j].rstrip('\n'))
            if m:
                cond = f'{i}  if:{m.group(1)}\n'
                break
        lineas.insert(paso, PASO.format(i=i, cond=cond, accion=ACCION))
    return ''.join(lineas)


def pendientes(root: Path = ROOT) -> list[str]:
    fuera = []
    for wf in sorted((root / '.github/workflows').glob('*.yml')):
        texto = wf.read_text(encoding='utf-8')
        if adoptar(texto) != texto:
            fuera.append(wf.name)
    return fuera


def main(argv: list[str]) -> int:
    if '--check' in argv:
        fuera = pendientes()
        for nombre in fuera:
            print(f'FALTA la acción materializar: {nombre}')
        return 1 if fuera else 0
    for wf in sorted((ROOT / '.github/workflows').glob('*.yml')):
        texto = wf.read_text(encoding='utf-8')
        nuevo = adoptar(texto)
        if nuevo != texto:
            wf.write_text(nuevo, encoding='utf-8')
            print(f'adoptada: {wf.name}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
