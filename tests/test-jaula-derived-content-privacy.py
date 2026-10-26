from pathlib import Path
from html.parser import HTMLParser
import json

ROOT = Path(__file__).resolve().parents[1]
PAGE = 'donde-empieza-la-jaula/index.html'

class Excerpt(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inside = False
        self.depth = 0
        self.paragraph = False
        self.paragraphs = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if not self.inside and tag == 'div' and 'excerpt-field' in a.get('class', '').split():
            self.inside = True
            self.depth = 1
        elif self.inside:
            if tag == 'div':
                self.depth += 1
            if tag == 'p':
                self.paragraph = True
    def handle_endtag(self, tag):
        if self.inside and tag == 'p':
            self.paragraph = False
        if self.inside and tag == 'div':
            self.depth -= 1
            if self.depth == 0:
                self.inside = False
    def handle_data(self, data):
        if self.inside and self.paragraph and data.strip():
            self.paragraphs.append(data.strip())

registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
entries = [e for e in registry['entries'] if e.get('sourceFile') == PAGE]
assert len(entries) == 1, f'{PAGE}: registro editorial inexistente o duplicado'
assert entries[0].get('status') != 'public', f'{PAGE}: esta prueba solo corresponde a contenido no publicado'
parser = Excerpt()
parser.feed((ROOT / PAGE).read_text(encoding='utf-8'))
phrases = [p for p in parser.paragraphs if len(p) >= 65][:8]
assert len(phrases) >= 3, f'{PAGE}: no se han extraído suficientes párrafos reales'
artifacts = ['llms.txt', 'llms-full.txt', 'sitemap.xml', 'robots.txt', 'data/navigation.json']
for name in artifacts:
    path = ROOT / name
    assert path.is_file(), f'{PAGE}: falta artefacto esperado {name}'
    content = path.read_text(encoding='utf-8')
    for phrase in phrases:
        assert phrase not in content, f'{name}: filtración de texto de {PAGE}: {phrase[:65]!r}'
print('OK: el capítulo de Jaula no aparece en artefactos públicos auxiliares')