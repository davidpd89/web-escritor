from html.parser import HTMLParser
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

class Head(HTMLParser):
    def __init__(self):
        super().__init__()
        self.lang = ''
        self.title = ''
        self.description = ''
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'html':
            self.lang = a.get('lang', '')
        elif tag == 'title':
            self.in_title = True
        elif tag == 'meta' and a.get('name') == 'description':
            self.description = a.get('content', '')

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data

CASES = {
    '404.html': (r'p[aá]gina no encontrada', r'direcci[oó]n solicitada|no existe'),
    'offline.html': (r'sin conexi[oó]n', r'no hay conexi[oó]n|sin conexi[oó]n'),
}
for page, (title_pattern, description_pattern) in CASES.items():
    parser = Head()
    parser.feed((ROOT / page).read_text(encoding='utf-8'))
    assert parser.lang.lower().split('-')[0] == 'es', f'{page}: idioma declarado incorrecto: {parser.lang!r}'
    assert re.search(title_pattern, parser.title, re.I), f'{page}: título de recuperación no reconocible en español: {parser.title!r}'
    assert re.search(description_pattern, parser.description, re.I), f'{page}: descripción de recuperación no reconocible en español: {parser.description!r}'
print('PASS: idioma y mensajes de recuperación coherentes')
