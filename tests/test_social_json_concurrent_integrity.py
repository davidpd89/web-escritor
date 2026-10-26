import concurrent.futures
import http.server
import json
import os
from pathlib import Path
import sys
import threading
import unittest
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/research'))
import gpt_social_compose as compose

class Quiet(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)
    def log_message(self, *args):
        pass

class ConcurrentJsonTests(unittest.TestCase):
    def test_public_snapshot_concurrent_readers(self):
        server = None
        origin = os.environ.get('QA_ORIGIN')
        if not origin:
            server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Quiet)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            origin = f'http://127.0.0.1:{server.server_port}'
        url = origin.rstrip('/') + '/redes-sociales/social-metrics.json'
        try:
            def read(i):
                with urlopen(url, timeout=15) as response:
                    self.assertEqual(response.status, 200, f'{url}, petición {i}: HTTP inesperado')
                    raw = response.read()
                self.assertTrue(raw, f'{url}, petición {i}: JSON vacío')
                data = json.loads(raw)
                networks = data['networks']
                actual = {n['id']: n['profile_url'] for n in networks}
                self.assertEqual(len(networks), len(compose.PROFILES), f'{url}, petición {i}: número incorrecto de redes')
                self.assertEqual(actual, compose.PROFILES, f'{url}, petición {i}: identidad pública incorrecta')
                active = [n for n in networks if n['status'] == 'ok']
                self.assertEqual(data['totals']['follower_relationships'], sum(n['followers'] for n in active), f'{url}, petición {i}: suma incoherente')
                self.assertEqual(data['totals']['coverage'], len(active), f'{url}, petición {i}: cobertura incoherente')
                self.assertEqual(data['totals']['eligible'], len(compose.PROFILES), f'{url}, petición {i}: elegibilidad incoherente')
                return raw
            with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
                results = list(pool.map(read, range(64)))
            self.assertTrue(all(result == results[0] for result in results), f'{url}: el snapshot cambió durante la lectura concurrente')
        finally:
            if server:
                server.shutdown()
                server.server_close()

if __name__ == '__main__':
    unittest.main()
