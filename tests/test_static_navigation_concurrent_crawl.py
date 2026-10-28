import concurrent.futures
import http.server
from html.parser import HTMLParser
import os
from pathlib import Path
import threading
import unittest
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
ROUTES = ('/', '/redes-sociales/', '/libros/', '/recomendaciones/')

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = 0
        self.h1 = 0
        self.links = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'title':
            self.title += 1
        if tag == 'h1':
            self.h1 += 1
        if tag == 'a' and attrs.get('href', '').startswith('/'):
            self.links.append(attrs['href'])

class Quiet(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)
    def log_message(self, *args):
        pass

class StaticNavigationTests(unittest.TestCase):
    def test_concurrent_pages_have_useful_nojs_navigation(self):
        server = None
        origin = os.environ.get('QA_ORIGIN')
        if not origin:
            server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Quiet)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            origin = f'http://127.0.0.1:{server.server_port}'
        try:
            def check(item):
                route, attempt = item
                url = origin.rstrip('/') + route
                with urlopen(url, timeout=20) as response:
                    self.assertEqual(response.status, 200, f'{route}, intento {attempt}: HTTP incorrecto')
                    body = response.read()
                self.assertGreater(len(body), 1000, f'{route}, intento {attempt}: HTML vacío o truncado')
                parser = Page()
                parser.feed(body.decode('utf-8'))
                self.assertEqual(parser.title, 1, f'{route}, intento {attempt}: title={parser.title}')
                self.assertEqual(parser.h1, 1, f'{route}, intento {attempt}: h1={parser.h1}')
                self.assertTrue(parser.links, f'{route}, intento {attempt}: no existen enlaces internos sin JS')
                return route, body
            requests = [(route, i) for i in range(12) for route in ROUTES]
            with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
                results = list(pool.map(check, requests))
            for route in ROUTES:
                bodies = [body for current, body in results if current == route]
                self.assertTrue(all(body == bodies[0] for body in bodies), f'{route}: HTML inconsistente durante peticiones simultáneas')
        finally:
            if server:
                server.shutdown()
                server.server_close()

if __name__ == '__main__':
    unittest.main()
