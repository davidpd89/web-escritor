import json
import unittest
from pathlib import Path
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://davidportodiaz.com/'

class TestBookShortcuts(unittest.TestCase):
    def test_manifest_book_shortcuts(self):
        manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
        shortcuts = manifest.get('shortcuts', [])
        self.assertTrue(shortcuts, 'manifest.json: no hay accesos directos declarados')
        checked = 0
        for shortcut in shortcuts:
            target = shortcut.get('url', '')
            parsed = urlsplit(urljoin(ORIGIN, target))
            with self.subTest(shortcut=shortcut.get('name'), url=target):
                self.assertEqual(parsed.scheme, 'https', f'manifest.json: protocolo inseguro: {target}')
                self.assertEqual(parsed.netloc, 'davidportodiaz.com', f'manifest.json: acceso fuera del sitio: {target}')
                self.assertFalse(parsed.username or parsed.password, f'manifest.json: credenciales en acceso: {target}')
                self.assertFalse(parsed.query, f'manifest.json: parámetros inesperados: {target}')
                self.assertFalse(parsed.fragment, f'manifest.json: fragmento inesperado: {target}')
                route = parsed.path.lstrip('/')
                destination = ROOT / route
                if route.endswith('/') or not destination.suffix:
                    destination = destination / 'index.html'
                self.assertTrue(destination.is_file(), f'manifest.json: destino inexistente: {target}')
                if route.startswith(('libros/', 'las-manecillas-del-recuerdo/')):
                    checked += 1
        self.assertGreater(checked, 0, 'manifest.json: no se encontraron accesos bibliográficos')

if __name__ == '__main__':
    unittest.main()