import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGE = 'mapa-del-sitio/index.html'

class DocumentParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.metas = []
        self.links = []
        self.scripts = []
        self.title = ''
        self.capture = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            self.metas.append(attrs)
        elif tag == 'link':
            self.links.append(attrs)
        elif tag == 'title':
            self.capture = ['title', '']
        elif tag == 'script' and attrs.get('type', '').lower() == 'application/ld+json':
            self.capture = ['jsonld', '']

    def handle_data(self, data):
        if self.capture:
            self.capture[1] += data

    def handle_endtag(self, tag):
        if self.capture and ((tag == 'title' and self.capture[0] == 'title') or (tag == 'script' and self.capture[0] == 'jsonld')):
            kind, value = self.capture
            if kind == 'title':
                self.title = value.strip()
            else:
                self.scripts.append(value)
            self.capture = None

p = DocumentParser()
p.feed((ROOT / PAGE).read_text(encoding='utf-8'))
assert p.title, f'{PAGE}: falta title'
descriptions = [m.get('content', '').strip() for m in p.metas if m.get('name', '').lower() == 'description']
assert len(descriptions) == 1 and descriptions[0], f'{PAGE}: description ausente o duplicada: {descriptions}'
canonicals = [link.get('href', '') for link in p.links if 'canonical' in link.get('rel', '').lower().split()]
assert canonicals == ['https://davidportodiaz.com/mapa-del-sitio/'], f'{PAGE}: canonical incorrecto: {canonicals}'
robots = [m.get('content', '').lower() for m in p.metas if m.get('name', '').lower() == 'robots']
assert robots and all('noindex' not in r for r in robots), f'{PAGE}: robots impide indexación: {robots}'
policies = [m.get('content', '') for m in p.metas if m.get('http-equiv', '').lower() == 'content-security-policy']
assert len(policies) == 1, f'{PAGE}: número incorrecto de políticas CSP: {len(policies)}'
policy = policies[0]
for directive in ('default-src', 'script-src', 'object-src', 'base-uri'):
    assert directive in policy, f'{PAGE}: falta directiva CSP {directive}'
assert "object-src 'none'" in policy, f'{PAGE}: object-src no bloquea objetos'
assert 'unsafe-eval' not in policy and 'unsafe-inline' not in policy, f'{PAGE}: CSP permite ejecución insegura'
assert p.scripts, f'{PAGE}: no contiene JSON-LD'
for index, script in enumerate(p.scripts):
    data = json.loads(script)
    assert isinstance(data, (dict, list)), f'{PAGE}: JSON-LD {index} sin estructura válida'
print('PASS: metadatos SEO, canonical, CSP y JSON-LD del mapa del sitio')
