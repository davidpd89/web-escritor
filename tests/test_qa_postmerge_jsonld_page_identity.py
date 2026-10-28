import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class HeadData(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonicals = []
        self.blocks = []
        self.inside = False
        self.parts = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'link' and 'canonical' in a.get('rel', '').lower().split():
            self.canonicals.append(a.get('href'))
        if tag == 'script' and a.get('type', '').lower() == 'application/ld+json':
            self.inside = True
            self.parts = []
    def handle_data(self, data):
        if self.inside:
            self.parts.append(data)
    def handle_endtag(self, tag):
        if tag == 'script' and self.inside:
            self.blocks.append(json.loads(''.join(self.parts)))
            self.inside = False

def nodes(value):
    if isinstance(value, list):
        for item in value:
            yield from nodes(item)
    elif isinstance(value, dict):
        yield value
        if '@graph' in value:
            yield from nodes(value['@graph'])

for rel in ('cuaderno/index.html', 'editoriales/index.html', 'recomendaciones/index.html'):
    parser = HeadData()
    parser.feed((ROOT / rel).read_text(encoding='utf-8'))
    assert len(parser.canonicals) == 1, f'{rel}: canonical duplicado o ausente: {parser.canonicals!r}'
    canonical = parser.canonicals[0]
    collections = [node for block in parser.blocks for node in nodes(block) if 'CollectionPage' in ([node.get('@type')] if isinstance(node.get('@type'), str) else node.get('@type', []))]
    assert collections, f'{rel}: falta CollectionPage en JSON-LD'
    for node in collections:
        assert node.get('url') == canonical, f'{rel}: CollectionPage.url={node.get("url")!r}, canonical={canonical!r}'
        identifier = node.get('@id', '')
        assert identifier == canonical or identifier.startswith(canonical + '#'), f'{rel}: @id contradictorio: {identifier!r}'
print('OK: CollectionPage y canonical coherentes')