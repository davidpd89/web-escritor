#!/usr/bin/env python3
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTE = '/publicar-web/'
html = (ROOT / 'publicar-web/index.html').read_text(encoding='utf-8')
assert 'noindex' in html.lower()

content = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
assert not [e for e in content['entries'] if e.get('url') == ROUTE and e.get('status', content.get('defaults', {}).get('status', 'public')) == 'public']

tools = json.loads((ROOT / 'data/tools-hub.json').read_text(encoding='utf-8'))
assert all(item.get('href') != ROUTE for item in tools['tools'] + tools.get('directories', []))

sitemap = ET.parse(ROOT / 'sitemap.xml')
locations = [e.text or '' for e in sitemap.iter() if e.tag.endswith('}loc') or e.tag == 'loc']
assert locations, 'Sitemap sin URLs'
assert not any(url.rstrip('/') == 'https://davidportodiaz.com/publicar-web' for url in locations)

for relative in ('llms.txt', 'llms-full.txt', 'herramientas/index.html'):
    text = (ROOT / relative).read_text(encoding='utf-8')
    assert 'href="/publicar-web/"' not in text, relative
    assert 'https://davidportodiaz.com/publicar-web/' not in text, relative

print('PASS publicar-web: no se anuncia como destino público')
