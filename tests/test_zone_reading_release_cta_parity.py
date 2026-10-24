import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('zone_release', ROOT / 'scripts/build-reading-catalogue.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
source = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
books = [x for x in source['libros'] if x['estado'] == 'publicado']
coming = mod.upcoming_books(books)
ics = (ROOT / 'recomendaciones/proximos-lanzamientos.ics').read_text(encoding='utf-8')
unfolded = ics.replace('\r\n ', '').replace('\r\n', '\n')
assert unfolded.count('BEGIN:VEVENT') == len(coming)
for b in coming:
    assert unfolded.count('UID:' + b['id'].lower() + '@davidportodiaz.com') == 1
    assert 'DTSTART;VALUE=DATE:' + b['fecha_publicacion'].replace('-', '') in unfolded
    detail = (ROOT / mod.url(b).lstrip('/') / 'index.html').read_text(encoding='utf-8')
    assert 'href="/recomendaciones/proximos-lanzamientos.ics"' in detail
print('release CTA calendar parity: OK')
