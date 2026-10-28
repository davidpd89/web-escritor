from datetime import date
from pathlib import Path
import copy
import json
import runpy
import tempfile

ROOT = Path(__file__).resolve().parents[1]
reading = runpy.run_path(str(ROOT / 'scripts/build-reading-list.py'))
writer = runpy.run_path(str(ROOT / 'scripts/build-writer-tools.py'))
atlas = runpy.run_path(str(ROOT / 'scripts/build-atlas-literario.py'))

def must_reject(action, label):
    try:
        action()
    except ValueError:
        return
    raise AssertionError(f'{label}: URL con credenciales aceptada')

for bad_url in ['https://usuario:clave@example.org/recurso', 'https://editorial.example@destino.example/ficha']:
    item = {'id': 'prueba-lectura', 'publish': True, 'title': 'Lectura', 'author': 'Autor', 'note': 'Una reseña propia con suficientes observaciones sobre ritmo, trama, prosa y personajes para justificar su publicación.', 'status': 'reading', 'link_kind': 'official', 'url': bad_url, 'verified_on': '2026-10-20'}
    must_reject(lambda: reading['validate']({'items': [item]}, date(2026, 10, 23)), 'lecturas')

    writer_data = json.loads((ROOT / 'data/writer-tools.json').read_text(encoding='utf-8'))
    writer_data['tools'][0]['website'] = bad_url
    must_reject(lambda: writer['validate'](writer_data), 'directorio de herramientas')

    atlas_data = json.loads((ROOT / 'data/atlas-literario.json').read_text(encoding='utf-8'))
    atlas_data['items'][0]['source_urls'] = [bad_url]
    with tempfile.TemporaryDirectory() as temporary:
        source = Path(temporary) / 'atlas.json'
        source.write_text(json.dumps(atlas_data, ensure_ascii=False), encoding='utf-8')
        must_reject(lambda: atlas['load'](source), 'Atlas literario')
print('PASS: URLs externas sin credenciales ni host engañoso')
