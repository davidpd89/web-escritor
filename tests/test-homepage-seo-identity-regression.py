from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://davidportodiaz.com/'

class HeadParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.metas = []
        self.titles = []
        self.in_title = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'link': self.links.append(a)
        if tag == 'meta': self.metas.append(a)
        if tag == 'title': self.in_title = True
    def handle_endtag(self, tag):
        if tag == 'title': self.in_title = False
    def handle_data(self, data):
        if self.in_title: self.titles.append(data)

p = HeadParser()
p.feed((ROOT / 'index.html').read_text(encoding='utf-8'))
canon = [a.get('href') for a in p.links if 'canonical' in a.get('rel', '').lower().split()]
og = [a.get('content') for a in p.metas if a.get('property', '').lower() == 'og:url']
desc = [a.get('content', '').strip() for a in p.metas if a.get('name', '').lower() == 'description']
assert canon == [ORIGIN], f'index.html: canonical inesperado: {canon!r}'
assert og == [ORIGIN], f'index.html: og:url inesperado: {og!r}'
assert len(desc) == 1 and desc[0], f'index.html: description inválida: {desc!r}'
assert ''.join(p.titles).strip(), 'index.html: falta title'
xml = ET.parse(ROOT / 'sitemap.xml').getroot()
locs = [e.text for e in xml.iter() if e.tag.rsplit('}', 1)[-1] == 'loc']
assert locs.count(ORIGIN) == 1, f'sitemap.xml: portada {ORIGIN} aparece {locs.count(ORIGIN)} veces'
assert urlsplit(canon[0]).fragment == '', f'index.html: canonical con fragmento: {canon[0]}'
print('OK: identidad SEO de portada')