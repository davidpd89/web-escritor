import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from reading_editorial_sources import SourceError
from reading_planeta_source import planeta_edition

URL = 'https://www.planetadelibros.com/libro-cosamala/458658'
PAGE = (ROOT / 'tests/fixtures/planeta-ficha-cosamala.html').read_text(encoding='utf-8')
OFFICIAL = 'https://www.planetadelibros.com/autor/alana-s-portero/000059415'


class PlanetaAuthorURLIntegrityTests(unittest.TestCase):
    def test_insecure_and_credentialed_author_urls_are_rejected(self):
        baseline = planeta_edition(PAGE, URL)
        self.assertEqual(baseline['fuentes_autores']['Alana S. Portero'], OFFICIAL)
        invalid = (
            OFFICIAL.replace('https://', 'http://'),
            OFFICIAL.replace('https://', 'https://usuario:clave@'),
            OFFICIAL.replace('https://', 'https://usuario@'),
        )
        for candidate in invalid:
            with self.subTest(candidate=candidate):
                mutated = PAGE.replace(OFFICIAL, candidate, 1)
                self.assertNotEqual(mutated, PAGE)
                with self.assertRaises(SourceError):
                    planeta_edition(mutated, URL)


if __name__ == '__main__':
    unittest.main()
