import json
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://davidportodiaz.com'

class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.collect = False
        self.blocks = []
        self.canonical = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self.collect = True
            self.blocks.append('')
        if tag == 'link' and 'canonical' in (a.get('rel') or '').split():
            self.canonical.append(a.get('href'))
    def handle_data(self, data):
        if self.collect:
            self.blocks[-1] += data
    def handle_endtag(self, tag):
        if tag == 'script':
            self.collect = False

page = Document()
page.feed((ROOT / 'herramientas/index.html').read_text(encoding='utf-8'))
assert len(page.canonical) == 1, f'/herramientas/: canonical: {page.canonical}'
assert page.canonical[0] == ORIGIN + '/herramientas/', f'/herramientas/: canonical incorrecto: {page.canonical}'
entities = [json.loads(block) for block in page.blocks]
collections = [item for item in entities if item.get('@type') == 'CollectionPage']
assert len(collections) == 1, f'/herramientas/: CollectionPage encontrados: {len(collections)}'
collection = collections[0]
assert collection.get('url') == page.canonical[0], f'/herramientas/: URL JSON-LD diferente de canonical: {collection.get("url")}'
items = collection['mainEntity']['itemListElement']
registry = json.loads((ROOT / 'data/tools-hub.json').read_text(encoding='utf-8'))
expected = {ORIGIN + tool['href'] for tool in registry['tools']}
actual = [item['url'] for item in items]
assert len(actual) == len(set(actual)), '/herramientas/: URL duplicadas en ItemList'
assert set(actual) == expected, f'/herramientas/: diferencias JSON-LD/registro: faltan={sorted(expected-set(actual))}; sobran={sorted(set(actual)-expected)}'
for index, item in enumerate(items, 1):
    url = item['url']
    parsed = urlsplit(url)
    assert parsed.scheme == 'https' and parsed.netloc == 'davidportodiaz.com' and not parsed.username and not parsed.password and not parsed.query and not parsed.fragment, f'/herramientas/: URL no autorizada: {url}'
    assert item['position'] == index, f'/herramientas/: posición {item["position"]}, esperada {index}'
assert collection['mainEntity']['numberOfItems'] == len(items), '/herramientas/: numberOfItems incorrecto'
print(f'OK: {len(items)} entidades JSON-LD autorizadas')
