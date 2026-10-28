from datetime import date
from pathlib import Path
import json
import re
import runpy

ROOT = Path(__file__).resolve().parents[1]
m = runpy.run_path(str(ROOT / 'scripts/build-reading-list.py'))
note = 'Una lectura con observaciones concretas sobre ritmo, personajes, construcción narrativa y decisiones de estilo.'
items = [
    {'id': 'lectura-antigua', 'publish': True, 'title': 'Lectura antigua', 'author': 'Autora Uno', 'note': note, 'status': 'finished', 'finished_on': '2026-09-01', 'link_kind': 'none'},
    {'id': 'lectura-reciente', 'publish': True, 'title': 'Lectura reciente', 'author': 'Autor Dos', 'note': note, 'status': 'finished', 'finished_on': '2026-10-01', 'link_kind': 'none'}
]
validated, disclosure = m['validate']({'items': items}, date(2026, 10, 23))
page = m['render'](validated, disclosure, '2026-10-23')
visible = re.findall(r'<h3>(.*?)</h3>', page, flags=re.S)
script = re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)
assert script, 'no hay ItemList JSON-LD'
structured = json.loads(script.group(1))['mainEntity']['itemListElement']
seo_order = [item['name'] for item in structured]
assert visible == ['Lectura reciente', 'Lectura antigua'], visible
assert seo_order == visible, f'orden visible={visible}, JSON-LD={seo_order}'
print('PASS: orden visible y estructurado coincidente')
