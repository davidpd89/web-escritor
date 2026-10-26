from html.parser import HTMLParser
from pathlib import Path
import re

PAGE = '/publicar-web/'
ROOT = Path(__file__).resolve().parents[1]

class Styles(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if tag == 'style':
            self.depth += 1
            self.blocks.append('')

    def handle_endtag(self, tag):
        if tag == 'style' and self.depth:
            self.depth -= 1

    def handle_data(self, data):
        if self.depth:
            self.blocks[-1] += data

p = Styles()
p.feed((ROOT / 'publicar-web/index.html').read_text(encoding='utf-8'))
assert p.blocks, f'{PAGE}: desapareció el CSS integrado de la página'
css = '\n'.join(p.blocks)
size = len(css.encode('utf-8'))
assert size <= 512, f'{PAGE}: CSS crítico {size} bytes, máximo 512'
assert not re.search(r'@import\b|url\s*\(', css, re.I), f'{PAGE}: CSS introduce una dependencia de red'
print(f'OK {PAGE}: CSS integrado de {size} bytes sin dependencias indirectas')
