"""Every public book stays reachable in bounded static catalogue pages."""
import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
expected = {b['id']: b for b in data['libros'] if b['estado'] == 'publicado'}
pages = [ROOT / 'recomendaciones/index.html', *sorted(ROOT.glob('recomendaciones/pagina/*/index.html'), key=lambda p: int(p.parent.name))]
routes = ['/recomendaciones/'] + [f'/recomendaciones/pagina/{p.parent.name}/' for p in pages[1:]]
budget = next(b for b in json.loads((ROOT / 'data/performance-budgets.json').read_text(encoding='utf-8'))['budgets'] if b['id'] == 'catalogue-html')['limits']['total_bytes']

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cards, self.links, self.blocks = [], [], []
        self.active, self.canonical, self.total, self.version = False, None, None, None
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'data-catalogue-book' in a:
            self.cards.append(a)
        if 'data-catalogue-page' in a:
            self.links.append(a['href'])
        if 'data-catalogue-version' in a:
            self.total, self.version = int(a['data-catalogue-total']), a['data-catalogue-version']
        if tag == 'link' and a.get('rel') == 'canonical':
            self.canonical = a['href']
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self.active = True
            self.blocks.append('')
    def handle_endtag(self, tag):
        if tag == 'script': self.active = False
    def handle_data(self, text):
        if self.active: self.blocks[-1] += text

ids, versions = [], set()
for path, route in zip(pages, routes):
    html = path.read_text(encoding='utf-8')
    page = Page(); page.feed(html)
    assert len(html.encode()) <= budget, path
    assert page.canonical == 'https://davidportodiaz.com' + route, path
    assert page.total == len(expected), path
    assert 0 <= len(page.cards) <= 96, path
    assert set(page.links) == set(routes) - {route}, path
    versions.add(page.version)
    itemlist = next(json.loads(b) for b in page.blocks if json.loads(b).get('@type') == 'ItemList')
    assert itemlist['numberOfItems'] == len(page.cards)
    assert len(itemlist['itemListElement']) == len(page.cards)
    for card, item in zip(page.cards, itemlist['itemListElement']):
        book = expected[card['data-book-id']]
        assert card['data-title'] == book['titulo']
        assert item['item']['name'] == book['titulo']
        assert item['item']['url'] == 'https://davidportodiaz.com/recomendaciones/libros/' + book['slug'] + '/'
        ids.append(card['data-book-id'])
assert len(ids) == len(set(ids)) == len(expected)
assert set(ids) == set(expected)
assert len(versions) == 1 and None not in versions
print(f'PASS static catalogue: {len(expected)} books, {len(pages)} bounded pages, unique canonicals and complete discovery')
