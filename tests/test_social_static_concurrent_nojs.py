import concurrent.futures
import http.server
import os
from pathlib import Path
import threading
import unittest
from urllib.request import urlopen
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]

class Structure(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1 = 0
        self.links = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'h1':
            self.h1 += 1
        if tag == 'a' and a.get('href', '').startswith('/'):
            self.links.append(a['href'])

class Quiet(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)
    def log_message(self, *args):
        pass

class StaticConcurrentTests(unittest.TestCase):
    def test_social_page_concurrent_without_javascript(self):
        server = None
        origin = os.environ.get('QA_ORIGIN')
        if not origin:
            server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Quiet)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            origin = f'http://127.0.0.1:{server.server_port}'
        try:
            def request(i):
                url = origin.rstrip('/') + '/redes-sociales/'
                with urlopen(url, timeout=15) as response:
                    status = response.status
                    body = response.read()
                self.assertEqual(status, 200, f'{url}, petición {i}: HTTP {status}')
                self.assertGreater(len(body), 1000, f'{url}, petición {i}: respuesta vacía o truncada')
                html = body.decode('utf-8')
                parser = Structure()
                parser.feed(html)
                self.assertEqual(parser.h1, 1, f'{url}, petición {i}: H1={parser.h1}')
                self.assertIn('/', parser.links, f'{url}, petición {i}: falta enlace de retorno al inicio')
                self.assertIn('/libros/', parser.links, f'{url}, petición {i}: falta navegación a obras')
                return body
            with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
                bodies = list(pool.map(request, range(48)))
            self.assertTrue(all(body == bodies[0] for body in bodies), '/redes-sociales/: respuestas HTML inconsistentes durante carga concurrente')
        finally:
            if server:
                server.shutdown()
                server.server_close()

if __name__ == '__main__':
    unittest.main()
