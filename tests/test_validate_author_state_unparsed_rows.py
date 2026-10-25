#!/usr/bin/env python3
"""Fixtures negativos contra el validador editorial real, sin red."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('vas', ROOT / 'scripts/validate-author-state.py')
vas = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = vas
SPEC.loader.exec_module(vas)

HEAD = (
    '---\nyear: "2026"\nstatus: published\nverified_at: "2026-10-24"\n'
    'title: "Estado del autor"\npublic_slug: estado-2026\n'
    'published_url: "https://davidportodiaz.com/cuaderno/estado-2026/"\n---\n\n'
    '# Estado del autor\n\n## Resumen del año\nResumen verificable.\n\n'
)

CASES = {
    'hito_sin_etiqueta': (
        '## Hitos verificados del año\n- Premio confirmado pero sin fuente\n\n'
        '## Previsiones\n- [target] Trabajar en otro libro\n'
    ),
    'prevision_sin_texto': (
        '## Hitos verificados del año\n- [verified] Obra publicada — fuente: /libros/\n\n'
        '## Previsiones\n- [confirmed]\n'
    ),
    'prevision_formato_libre': (
        '## Hitos verificados del año\n- [verified] Obra publicada — fuente: /libros/\n\n'
        '## Previsiones\n- Traducción confirmada para 2027\n'
    ),
}

with tempfile.TemporaryDirectory() as directory:
    for label, body in CASES.items():
        path = Path(directory) / (label + '.md')
        path.write_text(HEAD + body, encoding='utf-8')
        errors = vas.validate(path)
        assert errors, f'{label}: documento publicado inválido aceptado silenciosamente'
        print('PASS', label, errors)

print('PASS author-state parser rejection')