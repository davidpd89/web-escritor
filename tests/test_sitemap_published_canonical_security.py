import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'sitemap.xml'
assert path.is_file(), 'sitemap.xml: falta el artefacto publicado'
root = ET.parse(path).getroot()
namespace = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
locations = [element.text for element in root.findall('.//sm:url/sm:loc', namespace)]
assert locations, 'sitemap.xml: no contiene URLs indexables'

for location in locations:
    assert location and location.strip() == location, f'sitemap.xml: loc vacío o con espacios: {location!r}'
    parsed = urlsplit(location)
    assert parsed.scheme == 'https', f'sitemap.xml: esquema inseguro en {location}'
    assert parsed.netloc == 'davidportodiaz.com', f'sitemap.xml: autoridad no canónica en {location}'
    assert parsed.username is None and parsed.password is None, f'sitemap.xml: credenciales en {location}'
    assert parsed.port is None, f'sitemap.xml: puerto explícito en {location}'
    assert not parsed.query and not parsed.fragment, f'sitemap.xml: parámetros o fragmentos en {location}'
    assert parsed.path.startswith('/'), f'sitemap.xml: ruta no absoluta en {location}'
    assert not any(ord(character) < 32 or ord(character) == 127 for character in location), f'sitemap.xml: caracteres de control en {location!r}'

assert len(locations) == len(set(locations)), 'sitemap.xml: contiene URLs canónicas duplicadas'
print(f'PASS: {len(locations)} URLs canónicas seguras y únicas')
