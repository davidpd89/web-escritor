#!/usr/bin/env python3
import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class FormLabels(HTMLParser):
    def __init__(self):
        super().__init__()
        self.labels = set()
        self.controls = []
        self.depth = 0
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'label':
            self.depth += 1
            if a.get('for'):
                self.labels.add(a['for'])
        if tag in {'input', 'select', 'textarea'}:
            if a.get('type', '').lower() in {'hidden', 'submit', 'button', 'reset', 'image'}:
                return
            self.controls.append((tag, a, self.depth > 0))
    def handle_endtag(self, tag):
        if tag == 'label':
            self.depth = max(0, self.depth - 1)

registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
errors = []
count = 0
for raw in registry['entries']:
    entry = {**registry.get('defaults', {}), **raw}
    rel = entry.get('sourceFile', '')
    if entry['status'] != 'public' or not rel.endswith('.html') or not (ROOT / rel).is_file():
        continue
    parser = FormLabels()
    parser.feed((ROOT / rel).read_text(encoding='utf-8'))
    for tag, attrs, wrapped in parser.controls:
        count += 1
        named = wrapped or bool(attrs.get('id') in parser.labels) or bool(attrs.get('aria-label', '').strip()) or bool(attrs.get('aria-labelledby', '').strip())
        if not named:
            errors.append(f'{rel}: {tag}#{attrs.get("id", "sin-id")} sin nombre accesible')
assert count > 10, 'No se han encontrado suficientes campos'
assert not errors, '\n'.join(errors[:120])
print(f'OK etiquetas: {count} campos comprobados')
