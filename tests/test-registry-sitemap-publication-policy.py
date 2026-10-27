#!/usr/bin/env python3
"""Integración entre el registro editorial y el sitemap publicado."""
import json
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://davidportodiaz.com'
NS = '{http://www.sitemaps.org/schemas/sitemap/0.9}'

class Head(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.canonical = None
        self.noindex = False
        self.head = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'head':
            self.head = True
        elif tag == 'body':
            self.head = False
        if not self.head:
            return
        if tag == 'link' and 'canonical' in a.get('rel', '').lower().split():
            self.canonical = a.get('href')
        if tag == 'meta' and a.get('name', '').lower() == 'robots':
            self.noindex |= 'noindex' in [x.strip().lower() for x in a.get('content', '').split(',')]

registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
defaults = registry.get('defaults', {})
sitemap = ET.parse(ROOT / 'sitemap.xml').getroot()
urls = {e.findtext(NS + 'loc') for e in sitemap.findall(NS + 'url')}
errors = []
checked = 0
for entry in registry['entries']:
    # Los fragmentos editoriales no son páginas HTML independientes.
    # Su exclusión no determina la publicación del documento contenedor.
    if '#' in entry.get('url', ''):
        continue
    source = entry.get('sourceFile', '')
    if not source.endswith('.html'):
        continue
    path = ROOT / source
    if not path.is_file():
        continue
    head = Head()
    head.feed(path.read_text(encoding='utf-8'))
    if not head.canonical or not head.canonical.startswith(ORIGIN + '/'):
        continue
    status = entry.get('status', defaults.get('status', 'public'))
    enabled = entry.get('sitemap', defaults.get('sitemap', True))
    if status != 'public':
        continue
    checked += 1
    actual = head.canonical in urls
    expected = bool(enabled) and not head.noindex
    if actual != expected:
        errors.append(f"{source}: registro sitemap={enabled!r}, noindex={head.noindex}, canonical={head.canonical!r}, presente={actual}")
assert checked > 0, 'No se comprobaron páginas HTML públicas del registro'
if errors:
    sys.exit('POLÍTICA REGISTRO/SITEMAP:\n' + '\n'.join(errors))
print(f'OK: {checked} páginas públicas contrastadas con sitemap.xml')
