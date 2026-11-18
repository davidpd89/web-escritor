#!/usr/bin/env python3
"""Ningún job de un workflow privilegiado (workflow_run / pull_request_target) usa la caché de dependencias de setup-*.

Por qué: una caché que se escribe en un contexto privilegiado tras hacer checkout de un sha ajeno es
envenenable (CodeQL `actions/cache-poisoning/poisonable-step`). #1435 lo introdujo al llevar
`setup-python`/`setup-node` con `cache:` a una acción común que también usa la auditoría postdespliegue.
(Las cachés de navegadores Playwright con actions/cache son previas y CodeQL no las marca; quedan fuera.)
Se revisan los pasos del job y, recursivamente, los de las acciones locales (`./.github/actions/*`).
"""
from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PRIVILEGIADOS = {'workflow_run', 'pull_request_target'}


def triggers(doc: dict) -> set[str]:
    on = doc.get('on', doc.get(True))
    if isinstance(on, str):
        return {on}
    if isinstance(on, list):
        return set(on)
    return set(on or {})


def pasos_con_cache(pasos: list, origen: str, vistos: set[str]) -> list[str]:
    malos = []
    for paso in pasos or []:
        uses = str(paso.get('uses', ''))
        con = paso.get('with') or {}
        if uses.startswith(('actions/setup-python', 'actions/setup-node', 'actions/setup-go', 'actions/setup-java')) \
                and str(con.get('cache', '')).strip():
            malos.append(f'{origen}: {uses} con cache: {con["cache"]}')
        if uses.startswith('./') and uses not in vistos:
            vistos.add(uses)
            accion = ROOT / uses / 'action.yml'
            if accion.exists():
                doc = yaml.safe_load(accion.read_text(encoding='utf-8')) or {}
                malos += pasos_con_cache((doc.get('runs') or {}).get('steps'), uses, vistos)
    return malos


class PrivilegiadoSinCache(unittest.TestCase):
    def test_sin_cache_en_workflows_privilegiados(self):
        malos = []
        for wf in sorted((ROOT / '.github/workflows').glob('*.y*ml')):
            doc = yaml.safe_load(wf.read_text(encoding='utf-8')) or {}
            if not triggers(doc) & PRIVILEGIADOS:
                continue
            for nombre, job in (doc.get('jobs') or {}).items():
                malos += pasos_con_cache(job.get('steps'), f'{wf.name}:{nombre}', set())
        self.assertEqual(malos, [], 'Caché de dependencias en un workflow privilegiado (envenenable):\n' + '\n'.join(malos))

    def test_detecta_cache_en_accion_local(self):
        # La regla mira dentro de las acciones locales: simular un paso con cache: pip.
        malos = pasos_con_cache([{'uses': 'actions/setup-python@v6', 'with': {'cache': 'pip'}}], 'x', set())
        self.assertEqual(len(malos), 1)


if __name__ == '__main__':
    unittest.main()
