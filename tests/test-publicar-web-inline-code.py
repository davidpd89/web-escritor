#!/usr/bin/env python3
"""Comprueba la representación tipográfica de instrucciones técnicas reales."""
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'publicar-web/index.html'
SCRIPTS = (
    'scripts/build-sitemap.py',
    'scripts/validate_jsonld.py',
    'scripts/check-internal-graph.py',
)

class ContentParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.fragments = []

    def handle_starttag(self, tag, attrs):
        if tag not in {'meta', 'link', 'br', 'img', 'hr', 'input'}:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.stack:
            while self.stack:
                if self.stack.pop() == tag:
                    break

    def handle_data(self, data):
        if data.strip() and 'main' in self.stack:
            self.fragments.append((data, tuple(self.stack)))

parser = ContentParser()
parser.feed(PAGE.read_text(encoding='utf-8'))

for script in SCRIPTS:
    matches = [(text, ancestry) for text, ancestry in parser.fragments if script in text]
    assert matches, f'/publicar-web/: instrucción ausente: {script}'
    for text, ancestry in matches:
        assert '`' not in text, (
            f'/publicar-web/: {script} contiene delimitadores Markdown visibles: {text!r}'
        )
        assert 'code' in ancestry, (
            f'/publicar-web/: {script} debe presentarse como código HTML'
        )

print('PASS publicar-web: instrucciones técnicas sin Markdown literal')
