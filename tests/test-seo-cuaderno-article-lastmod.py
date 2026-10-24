#!/usr/bin/env python3
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
BLOCK = re.compile(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.I | re.S)
xml = ET.parse(ROOT / 'sitemap.xml')
checked = 0

for item in xml.findall('.//s:url', NS):
    url = item.findtext('s:loc', namespaces=NS) or ''
    pathname = urlsplit(url).path
    if not pathname.startswith('/cuaderno/') or '/temas/' in pathname or pathname == '/cuaderno/':
        continue
    target = ROOT / pathname.lstrip('/') / 'index.html'
    if not target.is_file():
        continue

    html = target.read_text(encoding='utf-8')
    for block in BLOCK.findall(html):
        document = json.loads(block)
        for node in document.get('@graph', [document]):
            if not isinstance(node, dict):
                continue
            types = node.get('@type', [])
            types = [types] if isinstance(types, str) else types
            if not any(t in ('Article', 'BlogPosting') for t in types):
                continue
            published = node.get('datePublished')
            modified = node.get('dateModified')
            assert published and modified, f'{pathname}: fechas editoriales ausentes'
            assert date.fromisoformat(published[:10]) <= date.fromisoformat(modified[:10]), pathname
            lastmod = item.findtext('s:lastmod', namespaces=NS)
            assert lastmod, f'{pathname}: artículo sin lastmod'
            assert lastmod[:10] == modified[:10], f'{pathname}: sitemap={lastmod}, JSON-LD={modified}'
            checked += 1

assert checked >= 4, f'Solo {checked} artículos comprobados'
print(f'OK: cronología y lastmod de {checked} artículos')
