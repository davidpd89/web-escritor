#!/usr/bin/env python3
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
BASE = 'https://davidportodiaz.com/editoriales/'

def entries(filename):
    tree = ET.parse(ROOT / filename)
    result = {}
    for node in tree.findall('.//s:url', NS):
        url = node.findtext('s:loc', namespaces=NS)
        date = node.findtext('s:lastmod', namespaces=NS)
        assert url, f'{filename}: loc vacío'
        assert url not in result, f'{filename}: URL duplicada: {url}'
        result[url] = date
    return result

main = entries('sitemap.xml')
editoriales = entries('editoriales-sitemap.xml')
assert editoriales, 'Sitemap editorial vacío'
assert all(url.startswith(BASE) for url in editoriales), 'Sitemap editorial contiene rutas ajenas'

missing = sorted(set(editoriales) - set(main))
assert not missing, f'Editoriales ausentes del sitemap general: {missing}'

mismatches = {
    url: {'general': main[url], 'editoriales': date}
    for url, date in editoriales.items()
    if url in main and main[url] != date
}
assert not mismatches, f'Fechas lastmod contradictorias: {mismatches}'

print(f'OK: {len(editoriales)} URLs editoriales mantienen paridad completa')
