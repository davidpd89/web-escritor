#!/usr/bin/env python3
"""Protege los enlaces de retorno desde el calendario de lanzamientos."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CALENDAR = ROOT / 'recomendaciones/proximos-lanzamientos.ics'
DATA = ROOT / 'data/reading-catalogue.json'

assert CALENDAR.is_file(), 'Falta recomendaciones/proximos-lanzamientos.ics'
books = json.loads(DATA.read_text(encoding='utf-8'))['libros']
published = {book['id'].lower(): book for book in books if book['estado'] == 'publicado'}
raw = CALENDAR.read_text(encoding='utf-8-sig')
lines = raw.replace('\r\n', '\n').replace('\r', '\n').split('\n')
unfolded = []
for line in lines:
    if line.startswith((' ', '\t')) and unfolded:
        unfolded[-1] += line[1:]
    else:
        unfolded.append(line)

errors = []
checked = 0
inside = False
fields = {}

for line in unfolded:
    if line == 'BEGIN:VEVENT':
        inside = True
        fields = {}
    elif line == 'END:VEVENT' and inside:
        checked += 1
        uid = fields.get('UID', '')
        identifier = uid.removesuffix('@davidportodiaz.com')
        book = published.get(identifier)
        if book is None:
            errors.append(f'{CALENDAR.relative_to(ROOT)}: UID sin libro publicado: {uid}')
        else:
            expected = 'https://davidportodiaz.com/recomendaciones/libros/' + book['slug'] + '/'
            actual = fields.get('URL')
            if actual != expected:
                errors.append(f'{CALENDAR.relative_to(ROOT)}: {uid}: URL {actual!r}; esperada {expected!r}')
            target = ROOT / 'recomendaciones/libros' / book['slug'] / 'index.html'
            if not target.is_file():
                errors.append(f'{CALENDAR.relative_to(ROOT)}: {uid}: ficha inexistente {target.relative_to(ROOT)}')
        inside = False
    elif inside and ':' in line:
        key, value = line.split(':', 1)
        fields[key] = value

assert not inside, f'{CALENDAR.relative_to(ROOT)}: VEVENT sin cierre'
assert not errors, '\n'.join(errors[:50])
print(f'PASS: {checked} enlaces de lanzamientos verificados; calendario vacío permitido')