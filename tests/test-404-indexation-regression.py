from html.parser import HTMLParser
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.robots = []
        self.descriptions = []
        self.titles = []
        self.in_title = False
        self.has_main = False
        self.has_html = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'html': self.has_html = True
        if tag == 'main': self.has_main = True
        if tag == 'title': self.in_title = True
        if tag == 'meta' and a.get('name', '').lower() == 'robots': self.robots.append(a.get('content', ''))
        if tag == 'meta' and a.get('name', '').lower() == 'description': self.descriptions.append(a.get('content', '').strip())
    def handle_endtag(self, tag):
        if tag == 'title': self.in_title = False
    def handle_data(self, data):
        if self.in_title: self.titles.append(data)

p = Parser()
p.feed((ROOT / '404.html').read_text(encoding='utf-8'))
assert p.has_html and p.has_main, '404.html: falta estructura HTML/main'
assert any('noindex' in [x.strip().lower() for x in value.split(',')] for value in p.robots), f'404.html: falta noindex: {p.robots!r}'
assert ''.join(p.titles).strip(), '404.html: falta title'
assert len(p.descriptions) == 1 and p.descriptions[0], f'404.html: description inválida: {p.descriptions!r}'
root = ET.parse(ROOT / 'sitemap.xml').getroot()
locs = [e.text or '' for e in root.iter() if e.tag.rsplit('}', 1)[-1] == 'loc']
assert not any(x.rstrip('/').endswith('/404') or x.rstrip('/').endswith('/404.html') for x in locs), 'sitemap.xml: contiene la página 404'
print('OK: 404 excluida del índice')