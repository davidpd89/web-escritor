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
        super().__init__()
        self.canonicals = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'link' and 'canonical' in a.get('rel', '').lower().split():
            self.canonicals.append(a.get('href'))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)
    def log_message(self, *args):
        pass

server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
base = 'http://127.0.0.1:' + str(server.server_port)

try:
    sitemap = ET.parse(ROOT / 'sitemap.xml')
    urls = [n.text for n in sitemap.findall('.//s:loc', NS)]
    assert urls, 'sitemap.xml: ninguna URL indexable'
    assert len(urls) == len(set(urls)), 'sitemap.xml: URL duplicadas'

    def check(url):
        parsed = urllib.parse.urlsplit(url)
        assert parsed.netloc == 'davidportodiaz.com', f'{url}: dominio inesperado'
        target = base + parsed.path
        with urllib.request.urlopen(target, timeout=15) as response:
            status = response.status
            body = response.read()
            content_type = response.headers.get('Content-Type', '')
        assert status == 200, f'{url}: HTTP {status}'
        assert 'text/html' in content_type, f'{url}: Content-Type {content_type}'
        assert len(body) > 100, f'{url}: HTML vacío o incompleto ({len(body)} bytes)'
        parser = Metadata()
        parser.feed(body.decode('utf-8'))
        assert parser.canonicals == [url], f'{url}: canonical {parser.canonicals!r}'
        return url

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(check, urls))
    assert len(results) == len(urls)
    print(f'PASS sitemap concurrent crawl: {len(results)} URL')
finally:
    server.shutdown()
    server.server_close()
