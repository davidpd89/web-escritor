import concurrent.futures
import http.server
import threading
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NS = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = []
        self.description = []
        self.canonical = []
        self.inside_title = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'title':
            self.inside_title = True
        if tag == 'meta' and a.get('name', '').lower() == 'description':
            self.description.append(a.get('content', ''))
        if tag == 'link' and 'canonical' in a.get('rel', '').lower().split():
            self.canonical.append(a.get('href', ''))
    def handle_data(self, data):
        if self.inside_title:
            self.title.append(data)
    def handle_endtag(self, tag):
        if tag == 'title':
            self.inside_title = False

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)
    def log_message(self, *args):
        pass

server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = 'http://127.0.0.1:' + str(server.server_port)

try:
    tree = ET.parse(ROOT / 'sitemap.xml')
    urls = [n.text for n in tree.findall('.//s:loc', NS)]
    assert urls, 'sitemap.xml: no hay URL'

    def check(url):
        path = urllib.parse.urlsplit(url).path
        with urllib.request.urlopen(base + path, timeout=15) as response:
            assert response.status == 200, f'{url}: HTTP {response.status}'
            payload = response.read()
        assert payload, f'{url}: respuesta vacía'
        meta = Metadata()
        meta.feed(payload.decode('utf-8'))
        title = ''.join(meta.title).strip()
        assert title, f'{url}: title vacío'
        assert len(meta.description) == 1 and meta.description[0].strip(), f'{url}: description ausente, vacía o duplicada: {meta.description!r}'
        assert meta.canonical == [url], f'{url}: canonical divergente: {meta.canonical!r}'
        return url

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        checked = list(pool.map(check, urls))
    assert len(checked) == len(urls)
    print(f'PASS concurrent SEO metadata: {len(checked)} URL')
finally:
    server.shutdown()
    server.server_close()
