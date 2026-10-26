#!/usr/bin/env python3
"""Protege los textos principales frente al truncamiento CSS explícito."""
from html.parser import HTMLParser
from pathlib import Path
import re

PAGE = Path(__file__).resolve().parents[1] / 'publicar-web/index.html'

class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.targets = []
        self.styles = []
        self.in_style = False

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == 'style':
            self.in_style = True
        if tag in {'h1', 'a'}:
            self.targets.append((tag, attributes.get('style', '')))
        if tag not in {'meta', 'link', 'br', 'img', 'hr', 'input'}:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag == 'style':
            self.in_style = False
        if tag in self.stack:
            while self.stack:
                if self.stack.pop() == tag:
                    break

    def handle_data(self, data):
        if self.in_style:
            self.styles.append(data)

parser = Parser()
parser.feed(PAGE.read_text(encoding='utf-8'))
assert any(tag == 'h1' for tag, _ in parser.targets), '/publicar-web/: falta H1'
assert any(tag == 'a' for tag, _ in parser.targets), '/publicar-web/: faltan enlaces'

for tag, style in parser.targets:
    assert not re.search(r'text-overflow\s*:\s*ellipsis|line-clamp\s*:', style, re.I), (
        f'/publicar-web/: {tag} contiene truncamiento inline: {style!r}'
    )

css = '\n'.join(parser.styles)
for rule in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
    selector, declarations = rule.groups()
    if not re.search(r'(^|[\s,>+~])(?:h1|a)(?=[\s,.:#\[>+~]|$)', selector, re.I):
        continue
    assert not re.search(r'text-overflow\s*:\s*ellipsis|(?:-webkit-)?line-clamp\s*:', declarations, re.I), (
        f'/publicar-web/: selector {selector.strip()!r} trunca texto: {declarations.strip()!r}'
    )

print('PASS publicar-web: sin truncamiento tipográfico explícito')
