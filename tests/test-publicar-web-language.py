#!/usr/bin/env python3
"""Detecta instrucciones inglesas en la checklist española."""
from html.parser import HTMLParser
from pathlib import Path
import re

PAGE = Path(__file__).resolve().parents[1] / 'publicar-web/index.html'

class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.items = []
        self.lang = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == 'html':
            self.lang = attributes.get('lang')
        if tag not in {'meta', 'link', 'br', 'img', 'hr', 'input'}:
            self.stack.append(tag)
        if tag == 'li':
            self.items.append([])

    def handle_endtag(self, tag):
        if tag in self.stack:
            while self.stack:
                if self.stack.pop() == tag:
                    break

    def handle_data(self, data):
        if 'li' in self.stack and self.items:
            self.items[-1].append(data)

parser = Parser()
parser.feed(PAGE.read_text(encoding='utf-8'))
assert parser.lang == 'es', f'/publicar-web/: lang inesperado: {parser.lang!r}'
items = [' '.join(parts) for parts in parser.items]
assert items, '/publicar-web/: no se encontraron instrucciones'

technical = [item for item in items if 'scripts/' in item]
assert technical, '/publicar-web/: no se encontraron instrucciones técnicas'

for item in technical:
    assert not re.search(r'\buse\s+[`<]?scripts/', item, re.IGNORECASE), (
        f'/publicar-web/: instrucción inglesa visible en documento español: {item!r}'
    )

print('PASS publicar-web: instrucciones técnicas en español')
