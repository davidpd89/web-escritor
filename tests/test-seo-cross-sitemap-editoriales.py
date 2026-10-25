#!/usr/bin/env python3
from __future__ import annotations
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}


def read_sitemap(filename):
    root = ET.parse(ROOT / filename).getroot()
    result = []
    for entry in root.findall('s:url', NS):
        loc = entry.findtext('s:loc', namespaces=NS)
        lastmod = entry.findtext('s:lastmod', namespaces=NS)
        assert loc, f'{filename}: entrada sin loc'
        result.append((loc, lastmod))
    counts = Counter(loc for loc, _ in result)
    duplicates = [loc for loc, count in counts.items() if count > 1]
    assert not duplicates, f'{filename}: URL duplicadas: {duplicates[:20]}'
    return dict(result)

main = read_sitemap('sitemap.xml')
editoriales = read_sitemap('editoriales-sitemap.xml')
assert editoriales, 'Sitemap editorial vacío'

missing = sorted(set(editoriales) - set(main))
assert not missing, f'URL editoriales ausentes del sitemap principal: {missing[:30]}'

mismatch = [(url, main[url], date) for url, date in editoriales.items() if main[url] != date]
assert not mismatch, f'Fechas lastmod divergentes: {mismatch[:30]}'

extra = sorted(url for url in main if '/editoriales/' in url and url not in editoriales)
assert not extra, f'Fichas editoriales ausentes del sitemap especializado: {extra[:30]}'

print(f'PASS cross-sitemap editorial parity: {len(editoriales)} URL')
