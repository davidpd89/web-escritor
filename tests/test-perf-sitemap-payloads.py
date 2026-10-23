#!/usr/bin/env python3
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
import gzip

ROOT = Path(__file__).resolve().parents[1]
NS = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
LIMIT_GZIP = 64 * 1024
LIMIT_URLS = 5000

for name in ('sitemap.xml', 'editoriales-sitemap.xml'):
    path = ROOT / name
    raw = path.read_bytes()
    tree = ET.fromstring(raw)
    assert tree.tag.endswith('urlset'), f'{name}: raíz XML inesperada'
    locations = [node.text for node in tree.findall('.//s:url/s:loc', NS)]
    assert locations, f'{name}: sitemap sin URLs'
    assert len(locations) == len(set(locations)), f'{name}: URLs duplicadas'
    assert len(locations) <= LIMIT_URLS, f'{name}: {len(locations)} entradas'
    for url in locations:
        parsed = urlsplit(url or '')
        assert parsed.scheme == 'https' and parsed.netloc == 'davidportodiaz.com', f'{name}: URL inválida {url}'
    packed = gzip.compress(raw, compresslevel=9, mtime=0)
    assert len(packed) <= LIMIT_GZIP, f'{name}: gzip={len(packed)} B'
    print(f'{name}: {len(locations)} URLs, raw={len(raw)} B, gzip={len(packed)} B')

print('PASS presupuestos sitemap')
