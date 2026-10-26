import concurrent.futures
import http.server
import json
import threading
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://davidportodiaz.com'

class SEO(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonical = []
        self.robots = []
        self.titles = []
        self.in_title = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'link' and 'canonical' in a.get('rel', '').lower().split():
            self.canonical.append(a.get('href'))
        if tag == 'meta' and a.get('name', '').lower() == 'robots':
            self.robots.append(a.get('content', ''))
        if tag == 'title':
            self.in_title = True
    def handle_data(self, data):
        if self.in_title:
            self.titles.append(data)
    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)
    def log_message(self, *args):
        pass

books = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))['libros']
published = [b for b in books if b['estado'] == 'publicado']
assert published, 'Catálogo sin libros publicados'
server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = 'http://127.0.0.1:' + str(server.server_port)

try:
    def check(book):
        path = '/recomendaciones/libros/' + book['slug'] + '/'
        expected = SITE + path
        with urllib.request.urlopen(base + path, timeout=15) as response:
            assert response.status == 200, f'{path}: HTTP {response.status}'
            body = response.read()
        assert len(body) > 100, f'{path}: respuesta vacía'
        parser = SEO()
        parser.feed(body.decode('utf-8'))
        assert parser.canonical == [expected], f'{path}: canonical {parser.canonical!r}'
        assert any(t.strip() for t in parser.titles), f'{path}: title vacío'
        assert not any('noindex' in [x.strip().lower() for x in r.split(',')] for r in parser.robots), f'{path}: noindex inesperado'
        return path

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        checked = list(pool.map(check, published))
    assert len(checked) == len(published)
    print(f'PASS reading concurrent SEO: {len(checked)} fichas')
finally:
    server.shutdown()
    server.server_close()
