import concurrent.futures
import hashlib
import http.server
import threading
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ('/robots.txt', '/sitemap.xml')

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)
    def log_message(self, *args):
        pass

server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = 'http://127.0.0.1:' + str(server.server_port)
expected = {path: hashlib.sha256((ROOT / path.lstrip('/')).read_bytes()).digest() for path in FILES}

try:
    def check(path):
        with urllib.request.urlopen(base + path, timeout=15) as response:
            assert response.status == 200, f'{path}: HTTP {response.status}'
            payload = response.read()
        assert payload, f'{path}: respuesta vacía'
        assert hashlib.sha256(payload).digest() == expected[path], f'{path}: contenido incompleto o alterado'
        if path == '/sitemap.xml':
            root = ET.fromstring(payload)
            ns = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
            urls = root.findall(ns + 'url')
            assert urls, f'{path}: XML sin URL'
            for node in urls:
                loc = node.find(ns + 'loc')
                assert loc is not None and loc.text, f'{path}: loc vacío'
        else:
            text = payload.decode('utf-8')
            assert 'Sitemap: https://davidportodiaz.com/sitemap.xml' in text, f'{path}: declaración Sitemap ausente'
            assert 'User-agent:' in text, f'{path}: directivas de rastreo ausentes'
        return path

    requests = list(FILES) * 20
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(check, requests))
    assert len(results) == 40
    print('PASS concurrent SEO discovery: 40 respuestas verificadas')
finally:
    server.shutdown()
    server.server_close()
