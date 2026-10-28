import importlib.util
import json
import re
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('zone_atlas', ROOT / 'scripts/build-atlas-literario.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
payload = {'version': 1, 'updated': '2026-10-20',
  'categories': [{'slug': 'bibliotecas', 'name': 'Bibliotecas'}],
  'items': [{'status': state, 'slug': slug, 'title': slug, 'category': 'bibliotecas',
    'relationship': 'library', 'summary': 'Lugar documentado', 'country': 'España',
    'source_urls': ['https://example.org/'], 'verified_date': '2026-10-20',
    'image': {'src': '/assets/atlas.webp', 'alt': 'Biblioteca', 'credit': 'Autor',
              'license': 'CC BY', 'source_url': 'https://example.org/imagen'}}
    for slug, state in [('biblioteca-publica', 'published'), ('biblioteca-oculta', 'planned')]]}
with tempfile.TemporaryDirectory() as folder:
    out = Path(folder)
    count = mod.build(payload, {'bibliotecas': 'Bibliotecas'}, out)
    doc = (out / 'index.html').read_text(encoding='utf-8')
    public = json.loads((out / 'atlas-literario-public.json').read_text(encoding='utf-8'))
    assert count == len(public['items']) == 1
    assert 'biblioteca-oculta' not in doc
    paths = re.findall(r'href="(/atlas-literario/[^"]+/)"', doc)
    assert paths and set(paths) == {'/atlas-literario/biblioteca-publica/'}
    for url in set(paths):
        assert (out / Path(url).relative_to('/atlas-literario') / 'index.html').is_file(), url
print('atlas published link closure: OK')
