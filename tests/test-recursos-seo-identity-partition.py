from html.parser import HTMLParser
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://davidportodiaz.com'
CASES = [
    ('/recursos/ficha-historia-objeto-heredado/', 'LearningResource', True),
    ('/recursos/herramientas-para-escritores/', 'CollectionPage', False),
]

class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta = []
        self.links = []
        self.schemas = []
        self.titles = []
        self.in_title = False
        self.in_schema = False
        self.buffer = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta': self.meta.append(a)
        if tag == 'link': self.links.append(a)
        if tag == 'title': self.in_title = True
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self.in_schema = True
            self.buffer = []

    def handle_data(self, value):
        if self.in_title: self.titles.append(value)
        if self.in_schema: self.buffer.append(value)

    def handle_endtag(self, tag):
        if tag == 'title': self.in_title = False
        if tag == 'script' and self.in_schema:
            self.schemas.append(json.loads(''.join(self.buffer)))
            self.in_schema = False

seen = {'title': set(), 'description': set(), 'canonical': set()}
for route, schema_type, indexable in CASES:
    p = Page()
    p.feed((ROOT / route.lstrip('/') / 'index.html').read_text(encoding='utf-8'))
    title = ''.join(p.titles).strip()
    descriptions = [m['content'].strip() for m in p.meta if m.get('name') == 'description']
    canonicals = [x['href'] for x in p.links if 'canonical' in x.get('rel', '').split()]
    assert title and len(descriptions) == 1 and descriptions[0], f'{route}: title o description ausente'
    assert canonicals == [ORIGIN + route], f'{route}: canonical={canonicals}'
    for key, value in [('title', title), ('description', descriptions[0]), ('canonical', canonicals[0])]:
        assert value not in seen[key], f'{route}: {key} duplicado: {value}'
        seen[key].add(value)
    robots = [m.get('content', '').lower() for m in p.meta if m.get('name') == 'robots']
    assert len(robots) == 1, f'{route}: robots ausente o duplicado'
    tokens = {t.strip() for t in robots[0].split(',')}
    assert ('noindex' not in tokens) == indexable, f'{route}: indexabilidad inesperada: {robots}'
    matches = []
    for schema in p.schemas:
        types = schema.get('@type', [])
        if isinstance(types, str): types = [types]
        if schema_type in types: matches.append(schema)
    assert len(matches) == 1, f'{route}: {schema_type} encontrados={len(matches)}'
    assert matches[0].get('url') == ORIGIN + route, f'{route}: URL de {schema_type} incorrecta'
    if schema_type == 'LearningResource':
        assert matches[0].get('isAccessibleForFree') is True, f'{route}: ficha gratuita mal declarada'
print('OK: identidad SEO diferenciada de los dos recursos')