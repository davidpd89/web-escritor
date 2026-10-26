from pathlib import Path
import importlib.util
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/build-feed.py'
FEED = ROOT / 'cuaderno/feed.xml'

spec = importlib.util.spec_from_file_location('root_feed_copy', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert FEED.is_file(), f'{FEED}: falta el RSS generado que se publica'
root = ET.parse(FEED).getroot()
assert root.tag == 'rss', f'{FEED}: el documento no es RSS'
channel = root.find('channel')
assert channel is not None, f'{FEED}: falta channel'
markers = module.STALE_CHANNEL_MARKERS
assert markers, f'{SCRIPT}: no hay marcadores de textos editoriales obsoletos'
for field in ('title', 'description'):
    value = channel.findtext(field, default='').strip()
    assert value, f'{FEED}: channel/{field} vacío'
    for marker in markers:
        assert marker.casefold() not in value.casefold(), f'{FEED}: channel/{field} conserva el texto editorial obsoleto {marker!r}: {value!r}'
print('PASS: RSS sin presentación editorial antigua en la cabecera')
