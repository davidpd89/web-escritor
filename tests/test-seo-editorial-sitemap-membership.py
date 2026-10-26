from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

def locations(name):
    root = ET.parse(ROOT / name).getroot()
    values = [(node.text or '').strip() for node in root.iter() if node.tag.rsplit('}', 1)[-1] == 'loc']
    assert values, f'{name}: sitemap sin URL'
    assert len(values) == len(set(values)), f'{name}: URL duplicadas'
    for value in values:
        parsed = urlsplit(value)
        assert parsed.scheme == 'https' and parsed.netloc == 'davidportodiaz.com', f'{name}: origen incorrecto: {value}'
        assert not parsed.query and not parsed.fragment, f'{name}: URL con parámetros o fragmento: {value}'
    return set(values)

main = locations('sitemap.xml')
editorial = locations('editoriales-sitemap.xml')
assert 'https://davidportodiaz.com/editoriales/' in editorial, 'editoriales-sitemap.xml: falta portada del directorio'
for url in sorted(editorial):
    assert urlsplit(url).path.startswith('/editoriales/'), f'editoriales-sitemap.xml: URL ajena a editoriales: {url}'
    assert url in main, f'editoriales-sitemap.xml: URL ausente del sitemap principal: {url}'
print(f'OK: {len(editorial)} URL editoriales incluidas en sitemap principal')