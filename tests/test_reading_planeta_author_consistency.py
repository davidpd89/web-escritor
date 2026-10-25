import sys
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from reading_planeta_source import planeta_edition

URL = 'https://www.planetadelibros.com/libro-cosamala/458658'
PAGE = (ROOT / 'tests/fixtures/planeta-ficha-cosamala.html').read_text(encoding='utf-8')


class PlanetaAuthorConsistencyTests(unittest.TestCase):
    def test_authors_and_sources_have_identical_keys(self):
        result = planeta_edition(PAGE, URL)
        authors = result['autores']
        sources = result['fuentes_autores']
        self.assertTrue(authors)
        self.assertEqual(len(authors), len(set(authors)))
        self.assertEqual(set(authors), set(sources))
        for author, source in sources.items():
            with self.subTest(author=author):
                parsed = urlsplit(source)
                self.assertEqual(parsed.scheme, 'https')
                self.assertEqual(parsed.hostname, 'www.planetadelibros.com')
                self.assertTrue(parsed.path.startswith('/autor/'))
                self.assertFalse(parsed.username)
                self.assertFalse(parsed.password)


if __name__ == '__main__':
    unittest.main()
