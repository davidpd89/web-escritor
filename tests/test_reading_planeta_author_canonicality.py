import sys
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from reading_planeta_source import planeta_edition

URL = 'https://www.planetadelibros.com/libro-cosamala/458658'
PAGE = (ROOT / 'tests/fixtures/planeta-ficha-cosamala.html').read_text(encoding='utf-8')
OFFICIAL = 'https://www.planetadelibros.com/autor/alana-s-portero/000059415'


class PlanetaAuthorCanonicalityTests(unittest.TestCase):
    def test_tracking_parameters_do_not_enter_author_sources(self):
        for suffix in ('?utm_source=externo', '#biografia', '?ref=tercero#datos'):
            with self.subTest(suffix=suffix):
                modified = PAGE.replace(OFFICIAL, OFFICIAL + suffix, 1)
                self.assertNotEqual(modified, PAGE)
                result = planeta_edition(modified, URL)
                source = result['fuentes_autores']['Alana S. Portero']
                parts = urlsplit(source)
                self.assertFalse(parts.query)
                self.assertFalse(parts.fragment)
                self.assertEqual(parts.path, urlsplit(OFFICIAL).path)


if __name__ == '__main__':
    unittest.main()
