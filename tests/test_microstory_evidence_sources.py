from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.items=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':self.items.append(dict(attrs))

def links(file):
    parser=Links();parser.feed((ROOT/file).read_text(encoding='utf-8'));return parser.items

story=links('al-otro-lado/index.html')
awards=links('premios.html')
external=[x for x in story if urlparse(x.get('href','')).hostname=='www.letrascomoespada.com']
assert len(external)==3, f'Se esperan tres fuentes oficiales enlazadas: {len(external)}'
urls={x['href'] for x in external}
assert len(urls)==3
assert any('ganadores-febrero2026' in x for x in urls)
assert any('finalistas-febrero2026' in x for x in urls)
assert any('memoria2026.php' in x for x in urls)
award_urls={x.get('href') for x in awards}
assert urls<=award_urls, 'Una fuente oficial ya no figura en Premios'
for link in external:
    assert link.get('target')=='_blank'
    assert {'noopener','noreferrer'}<=set(link.get('rel','').split())
print('PASS microstory evidence provenance')
