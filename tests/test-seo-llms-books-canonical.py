#!/usr/bin/env python3
import re
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
text = (ROOT / 'llms.txt').read_text(encoding='utf-8')
NS = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
sitemap = ET.parse(ROOT / 'sitemap.xml')
indexed = {n.text.strip() for n in sitemap.findall('.//s:url/s:loc', NS) if n.text}

works = ('Las manecillas del recuerdo', 'Samuel entre mundos')
for title in works:
    heading = '### ' + title
    assert heading in text, f'Obra ausente de llms.txt: {title}'
    section = text.split(heading, 1)[1].split('\n### ', 1)[0]
    match = re.search(r'^- Página oficial:\s*(https://\S+)', section, flags=re.M)
    assert match, f'{title}: falta URL oficial'
    url = match.group(1).strip()
    parsed = urlsplit(url)
    assert parsed.hostname == 'davidportodiaz.com', (title, url)
    assert url in indexed, f'{title}: URL oficial ausente de sitemap.xml: {url}'

    relative = parsed.path.lstrip('/')
    page = ROOT / relative / 'index.html' if parsed.path.endswith('/') else ROOT / relative
    assert page.is_file(), f'{title}: HTML oficial inexistente: {page}'
    html = page.read_text(encoding='utf-8')
    match_canonical = re.search(r'<link\b[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)', html, re.I)
    assert match_canonical, f'{title}: falta canonical'
    assert match_canonical.group(1) == url, f'{title}: canonical distinto de llms.txt'

print('OK: URLs oficiales de las dos obras coherentes entre LLM, HTML y sitemap')
