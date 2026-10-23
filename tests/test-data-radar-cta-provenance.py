from __future__ import annotations
import importlib.util
import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('radar_cta_qa', ROOT / 'scripts/build-radar-opportunities.py')
radar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(radar)

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a' and 'data-radar-source' in a:
            self.links.append(a)

raw = json.loads((ROOT / 'data/radar-opportunities.json').read_text(encoding='utf-8'))
count = 0
for item in raw['items']:
    if not item.get('published'):
        continue
    radar.validate(item)
    parser = Links()
    parser.feed(radar.card(item))
    assert len(parser.links) == 1, item['id']
    link = parser.links[0]
    assert link['href'] == item['source_url'], item['id']
    assert link['target'] == '_blank', item['id']
    assert {'noopener', 'noreferrer'} <= set(link.get('rel', '').split()), item['id']
    assert link['data-radar-source-type'] == item['type'], item['id']
    count += 1

print(f'OK: {count} fuentes y CTAs verificados')
