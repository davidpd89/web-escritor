import importlib.util
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / 'pagefind/eligible-manifest.json').read_text(encoding='utf-8'))
assert isinstance(manifest.get('eligible_pages'), list) or isinstance(manifest.get('pages'), list), 'Manifiesto Pagefind sin listado reconocible'
pages = set(manifest.get('eligible_pages', manifest.get('pages', [])))
assert pages, 'Manifiesto de búsqueda vacío'

namespace = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
sitemap = ET.parse(ROOT / 'sitemap.xml')
paths = [urlsplit(el.text).path for el in sitemap.findall('.//s:loc', namespace) if el.text]
assert len(paths) == len(set(paths)), 'Sitemap con destinos duplicados'
indexed = set(paths)

contract = {
    'libros/index.html': '/libros/',
    'cuaderno/index.html': '/cuaderno/',
    'editoriales/index.html': '/editoriales/',
    'herramientas/index.html': '/herramientas/',
    'eventos.html': '/eventos.html',
}
for source, route in contract.items():
    assert (ROOT / source).is_file(), source
    assert source in pages, f'{source}: ausente del manifiesto Pagefind'
    assert route in indexed, f'{source}: ausente del sitemap ({route})'

print('PASS cross-index publication for main families')
