import importlib.util
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_list', ROOT / 'scripts/build-reading-list.py')
reading = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reading)

class OutboundUrlMatrix(unittest.TestCase):
    def test_unsafe_https_urls_are_rejected(self):
        urls = [
            'https://usuario:clave@example.org/obra',
            'https://example.org@evil.example/obra',
            'https://example.org/obra\nOtro-campo',
            'https://example.org/obra\rOtro-campo',
            'https://example.org/obra\ttexto'
        ]
        for url in urls:
            with self.subTest(url=url):
                item = {'id': 'obra-prueba', 'title': 'Prueba', 'author': 'Autora', 'publish': True, 'note': 'Una nota editorial personal extensa y concreta que permite comprobar la validación de enlaces al publicar un libro.', 'status': 'reading', 'started_on': '2026-01-01', 'link_kind': 'official', 'url': url, 'verified_on': '2026-01-10'}
                with self.assertRaises(ValueError):
                    reading.validate({'items': [item]}, date(2026, 3, 1))

    def test_normal_https_is_accepted(self):
        item = {'id': 'obra-prueba', 'title': 'Prueba', 'author': 'Autora', 'publish': True, 'note': 'Nota editorial suficientemente larga que recoge una impresión concreta de lectura y evita datos vacíos.', 'status': 'reading', 'link_kind': 'official', 'url': 'https://editorial.example/obra', 'verified_on': '2026-01-10'}
        self.assertEqual(len(reading.validate({'items': [item]}, date(2026, 3, 1))[0]), 1)

if __name__ == '__main__':
    unittest.main()