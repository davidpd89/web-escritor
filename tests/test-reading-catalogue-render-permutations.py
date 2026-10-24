#!/usr/bin/env python3
import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_render_qa', ROOT / 'scripts/build-reading-catalogue.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
books = mod.validate(data, ROOT)[:12]
template = (ROOT / 'scripts/templates/reading-catalogue.html.tmpl').read_text(encoding='utf-8')
assert len(books) >= 5
original_data = copy.deepcopy(data)
outputs = []
for seed in range(8):
    selected = books[:]
    random.Random(seed).shuffle(selected)
    outputs.append(mod.render_hub(data, selected, template))
assert len(set(outputs)) == 1, 'El catálogo cambia con el orden de entrada'
assert outputs[0].count('data-catalogue-book ') == len(books)
assert 'application/ld+json' in outputs[0]
assert data == original_data, 'El renderizador mutó los datos de entrada'
print(f'PASS: {len(books)} libros, 8 permutaciones idénticas')
