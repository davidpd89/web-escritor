import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from reading_editorial_sources import SourceError
from reading_planeta_source import planeta_edition

URL = 'https://www.planetadelibros.com/libro-cosamala/458658'
PAGE = (ROOT / 'tests/fixtures/planeta-ficha-cosamala.html').read_text(encoding='utf-8')
OFFICIAL_AUTHOR = 'https://www.planetadelibros.com/autor/alana-s-portero/000059415'
AUTHOR_PATH = '/autor/alana-s-portero/000059415'


class PlanetaAuthorProvenanceTests(unittest.TestCase):
    def test_only_official_profile_can_establish_author_identity(self):
        self.assertEqual(PAGE.count(OFFICIAL_AUTHOR), 1)

        baseline = planeta_edition(PAGE, URL)
        self.assertEqual(baseline['autores'], ['Alana S. Portero'])
        self.assertEqual(
            baseline['fuentes_autores']['Alana S. Portero'],
            OFFICIAL_AUTHOR,
        )

        foreign_links = (
            'https://tercero.invalid' + AUTHOR_PATH,
            '//tercero.invalid' + AUTHOR_PATH,
        )

        for foreign in foreign_links:
            with self.subTest(foreign_author_link=foreign):
                mutated = PAGE.replace(OFFICIAL_AUTHOR, foreign, 1)
                self.assertNotEqual(mutated, PAGE)
                self.assertNotIn(OFFICIAL_AUTHOR, mutated)

                # Canonical, ISBN y demás datos siguen intactos.
                # Solo se retira la procedencia oficial de la autoría.
                with self.assertRaises(SourceError):
                    planeta_edition(mutated, URL)


if __name__ == '__main__':
    unittest.main()
