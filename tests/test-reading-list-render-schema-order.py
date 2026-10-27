import importlib.util
import json
import re
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_render_order', ROOT / 'scripts/build-reading-list.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

source = json.loads((ROOT / 'data/reading-list.json').read_text(encoding='utf-8'))
base = source['items'][0]

def book(identifier, title, status, finished=None):
    item = dict(base)
    item.update(id=identifier, title=title, publish=True, status=status, link_kind='none', url=None)
    item.pop('finished_on', None)
    if finished:
        item['finished_on'] = finished
    return item

items = [
    book('finished-old', 'Lectura terminada antigua', 'finished', '2026-07-10'),
    book('reading-current', 'Lectura actual', 'reading'),
    book('finished-new', 'Lectura terminada reciente', 'finished', '2026-08-10'),
    book('paused-book', 'Lectura en pausa', 'paused'),
]
rendered = mod.render(items, '', '2026-08-19')
visible = [unescape(title) for title in re.findall(r'<h3>(.*?)</h3>', rendered, re.S)]
match = re.search(r'<script type="application/ld\+json">(.*?)</script>', rendered, re.S)
assert match, 'lecturas/index.html: falta ItemList JSON-LD'
schema = json.loads(match.group(1))
entries = schema['mainEntity']['itemListElement']
structured = [entry['name'] for entry in entries]
expected = ['Lectura actual', 'Lectura terminada reciente', 'Lectura terminada antigua', 'Lectura en pausa']
assert visible == expected, f'lecturas/index.html: orden HTML incorrecto: {visible}'
assert structured == visible, f'lecturas/index.html: orden JSON-LD {structured} distinto del HTML {visible}'
assert [entry['position'] for entry in entries] == list(range(1, len(entries) + 1)), f'lecturas/index.html: posiciones ItemList incorrectas: {entries}'
print('PASS reading render and JSON-LD order')