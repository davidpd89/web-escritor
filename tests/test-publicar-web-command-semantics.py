#!/usr/bin/env python3
from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / 'publicar-web/index.html').read_text(encoding='utf-8')

class CodeParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.code = []
        self.visible = []

    def handle_starttag(self, tag, attrs):
        if tag == 'code':
            self.depth += 1

    def handle_endtag(self, tag):
        if tag == 'code':
            self.depth -= 1

    def handle_data(self, data):
        self.visible.append(data)
        if self.depth:
            self.code.append(data)

parser = CodeParser()
parser.feed(HTML)
visible = ' '.join(parser.visible)
code = ' '.join(parser.code)
references = set(re.findall(r'scripts/[\w.-]+\.py', visible))
assert references, 'No se encontraron instrucciones ejecutables'

errors = []
for reference in sorted(references):
    if reference not in code:
        errors.append(f'{reference}: falta marcado semántico code')
if '`' in visible:
    errors.append('El navegador presenta caracteres Markdown literales')

assert not errors, '\n'.join(errors)
print(f'PASS publicar-web: {len(references)} instrucciones con semántica HTML correcta')
