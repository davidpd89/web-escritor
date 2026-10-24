#!/usr/bin/env python3
import copy
import importlib.util
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_ics_qa', ROOT / 'scripts/build-reading-catalogue.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
seed = data['libros'][0]
books = []
for i, name in enumerate(['Á' * 80, 'La última estación', 'Épica, magia; mundos paralelos']):
    item = copy.deepcopy(seed)
    item.update(id=f'qa-ics-{i}', slug=f'qa-ics-{i}', titulo=name, fecha_publicacion=f'2099-01-0{i + 1}', fecha_actualizacion='2026-10-20', fecha_verificacion='2026-10-20')
    books.append(item)
outputs = [mod.render_release_ics(list(order)).encode('utf-8') for order in itertools.permutations(books)]
assert len(set(outputs)) == 1, 'El calendario depende del orden de los libros'
result = outputs[0]
assert result.count(b'BEGIN:VEVENT') == 3
assert b'\n' not in result.replace(b'\r\n', b''), 'Se detectaron saltos LF aislados'
for line in result.split(b'\r\n'):
    assert len(line) <= 75, f'Línea ICS de {len(line)} octetos'
assert result.endswith(b'END:VCALENDAR\r\n')
print('PASS: calendario reproducible y plegado UTF-8 válido')
