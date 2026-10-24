#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
html = (ROOT / 'publicar-web/index.html').read_text(encoding='utf-8')
assert 'href="/sitemap.xml"' in html
assert 'scripts/build-sitemap.py' in html

result = subprocess.run(
    [sys.executable, 'scripts/build-sitemap.py', '--check'],
    cwd=ROOT, capture_output=True, text=True, timeout=60,
)
assert result.returncode == 0, f'Sitemap desactualizado: {result.stdout}\n{result.stderr}'

root = ET.parse(ROOT / 'sitemap.xml').getroot()
assert root.tag.endswith('urlset'), root.tag
locations = [node.text for node in root.iter() if node.tag.endswith('loc')]
assert locations, 'Sitemap sin localizaciones'
assert all(url and url.startswith('https://davidportodiaz.com') for url in locations)
assert not any('/publicar-web/' in url for url in locations)

print(f'PASS publicar-web: sitemap reproducible con {len(locations)} URLs')
