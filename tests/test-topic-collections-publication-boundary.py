import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('topic_publication_boundary', ROOT / 'scripts/build-topic-collections.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

payload = json.loads((ROOT / 'data/topic-collections.json').read_text(encoding='utf-8'))
collections = mod.validate(payload)
by_slug = {item['slug']: item for item in collections}

assert by_slug['fantasia-de-portales']['status'] == 'ready', 'data/topic-collections.json: fantasia-de-portales ha perdido el estado ready'
assert by_slug['como-construi-noveris']['status'] == 'draft', 'data/topic-collections.json: como-construi-noveris no debe publicarse todavía'
assert len(by_slug['fantasia-de-portales']['items']) >= 3, 'data/topic-collections.json: la colección publicada carece de tres piezas'
assert len(by_slug['como-construi-noveris']['items']) == 2, 'data/topic-collections.json: cambió el número de piezas de Noveris; revisar el contrato editorial'

ready = [item for item in collections if item['status'] == 'ready']
assert 'fantasia-de-portales' in {item['slug'] for item in ready}, 'cuaderno/temas/: falta la colección publicada'
assert 'como-construi-noveris' not in {item['slug'] for item in ready}, 'cuaderno/temas/: un borrador aparece entre las colecciones publicables'

for coll in ready:
    for item in coll['items']:
        target = ROOT / item['url'].strip('/') / 'index.html'
        assert target.is_file(), f'cuaderno/temas/{coll["slug"]}/: destino publicado inexistente: {item["url"]}'

print('PASS topic publication boundary')