from html.parser import HTMLParser
from pathlib import Path
import re

PAGE = '/publicar-web/'
ROOT = Path(__file__).resolve().parents[1]

class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.social = []
        self.rendered = []
        self.css = ''
        self.in_style = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and a.get('property') == 'og:image':
            self.social.append(a.get('content', ''))
        if tag in ('img', 'picture', 'source', 'svg', 'canvas', 'video'):
            self.rendered.append(tag)
        if tag == 'link' and a.get('as', '').lower() == 'image' and 'preload' in a.get('rel', '').lower().split():
            self.rendered.append('image preload')
        if tag == 'style':
            self.in_style = True

    def handle_endtag(self, tag):
        if tag == 'style':
            self.in_style = False

    def handle_data(self, data):
        if self.in_style:
            self.css += data

p = Images()
p.feed((ROOT / 'publicar-web/index.html').read_text(encoding='utf-8'))
assert len(p.social) == 1 and p.social[0].startswith('https://'), f'{PAGE}: imagen Open Graph ausente o inválida: {p.social}'
assert not p.rendered, f'{PAGE}: imagen incorporada al renderizado: {p.rendered}'
assert not re.search(r'url\s*\(|image-set\s*\(', p.css, re.I), f'{PAGE}: CSS provoca descarga de imágenes'
print('OK publicar-web: imagen social preservada sin coste de descarga visual')
