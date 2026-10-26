from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title = []
        self.description = []
        self.robots = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'title':
            self.in_title = True
        if tag == 'meta':
            name = attrs.get('name', '').lower()
            if name == 'description':
                self.description.append(attrs.get('content', '').strip())
            if name == 'robots':
                self.robots.append(attrs.get('content', '').lower())
    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)

root = ET.parse(ROOT / 'sitemap.xml').getroot()
urls = [n.text.strip() for n in root.iter() if n.tag.rsplit('}',1)[-1] == 'loc' and n.text]
paths = sorted({urlsplit(url).path for url in urls if urlsplit(url).path.startswith('/editoriales/')})
assert paths, 'sitemap.xml: no se descubrieron editoriales'
seen_titles = {}
seen_descriptions = {}
checked = 0
for path in paths:
    source = ROOT / path.lstrip('/') / 'index.html'
    assert source.is_file(), f'{path}: HTML anunciado en sitemap pero ausente: {source}'
    parser = Metadata()
    parser.feed(source.read_text(encoding='utf-8'))
    robots = ','.join(parser.robots)
    if 'noindex' in [x.strip() for x in robots.split(',')]:
        continue
    title = ' '.join(''.join(parser.title).split())
    assert title, f'{path}: title vacío'
    assert len(parser.description) == 1 and parser.description[0], f'{path}: description ausente, vacía o duplicada: {parser.description}'
    for field, value, seen in [('title',title,seen_titles),('description',parser.description[0],seen_descriptions)]:
        key = value.casefold()
        assert key not in seen, f'{path}: {field} duplicado con {seen.get(key)}: {value}'
        seen[key] = path
    checked += 1
assert checked > 0, 'No se analizaron fichas editoriales indexables'
print(f'OK: {checked} páginas editoriales con title y description únicos')