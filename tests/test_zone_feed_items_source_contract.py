import importlib.util
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('zone_feed_data', ROOT / 'scripts/build-feed.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
wanted, _ = mod.collect_items()
expected = {x['url']: x for x in wanted if x.get('title') and x.get('url')}
root = ET.parse(ROOT / 'cuaderno/feed.xml').getroot()
actual = root.findall('./channel/item')
links = [node.findtext('link') for node in actual]
assert expected and len(actual) == len(expected) == len(set(links)), 'RSS incompleto o con duplicados'
for node in actual:
    href = node.findtext('link')
    source = expected[href]
    assert node.findtext('guid') == href
    assert node.findtext('title') == source['title']
    assert (node.findtext('description') or '') == (source.get('description') or '')
    if source.get('date') and mod.iso_to_rfc2822(source['date']):
        assert node.findtext('pubDate') == mod.iso_to_rfc2822(source['date'])
print('RSS source parity: OK')
