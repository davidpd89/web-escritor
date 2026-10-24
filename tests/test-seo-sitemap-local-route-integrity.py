#!/usr/bin/env python3
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://davidportodiaz.com'
NS = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

class Head(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonicals = []
        self.robots = []
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == 'link' and 'canonical' in values.get('rel', '').lower().split():
            self.canonicals.append(values.get('href'))
        if tag == 'meta' and values.get('name', '').lower() == 'robots':
            self.robots.append(values.get('content', ''))

xml = ET.parse(ROOT / 'sitemap.xml')
urls = [n.text.strip() for n in xml.findall('.//s:url/s:loc', NS) if n.text]
assert len(urls) >= 100
errors = []

for url in urls:
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.netloc != 'davidportodiaz.com' or parsed.query or parsed.fragment:
        errors.append(f'URL no canónica: {url}')
        continue
    relative = unquote(parsed.path).lstrip('/')
    file = ROOT / relative
    if parsed.path.endswith('/') or not relative:
        file = file / 'index.html'
    if not file.is_file():
        errors.append(f'HTML inexistente: {url}')
        continue
    head = Head()
    head.feed(file.read_text(encoding='utf-8'))
    if head.canonicals != [url]:
        errors.append(f'Canonical distinto: {url} -> {head.canonicals}')
    if any('noindex' in re.split(r'[,\s]+', value.lower()) for value in head.robots):
        errors.append(f'Noindex anunciado en sitemap: {url}')

assert not errors, '\n'.join(errors[:50])
print(f'OK: {len(urls)} URLs verificadas contra HTML local y canonical')
