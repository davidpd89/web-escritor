from html.parser import HTMLParser
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PAGES = ('index.html', '404.html', 'offline.html')
PATTERNS = [re.compile(p, re.I) for p in (r'\blorem ipsum\b', r'\btexto de prueba\b', r'\btexto pendiente\b', r'\bpendiente de redactar\b', r'\bcontenido de ejemplo\b', r'\b(?:TODO|FIXME):\s*(?:redactar|escribir|sustituir|revisar)\b', r'\[\[pendiente\]\]', r'\b(?:inserta|escribe) aqu[ií] (?:el|la|un|una)\b')]

class PublicText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'template', 'noscript'):
            self.stack.append(tag)
        if not self.stack and tag == 'meta':
            a = dict(attrs)
            if a.get('name') == 'description' or a.get('property') in ('og:title', 'og:description'):
                self.parts.append(a.get('content', ''))

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()

    def handle_data(self, data):
        if not self.stack:
            self.parts.append(data)

for page in PAGES:
    parser = PublicText()
    parser.feed((ROOT / page).read_text(encoding='utf-8'))
    text = ' '.join(parser.parts)
    assert text.strip(), f'{page}: contenido público vacío'
    for pattern in PATTERNS:
        match = pattern.search(text)
        assert not match, f'{page}: texto provisional publicado: {match.group(0) if match else ""}'
print('PASS: documentos raíz sin marcadores editoriales provisionales')
