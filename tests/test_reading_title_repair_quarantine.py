import sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reading_quarantine as q
from reading_titles import tidy_title


class TitleRepairTest(unittest.TestCase):
    def test_mojibake_and_leading_dot(self):
        raw = '.Reeducaci\xc3\xb3n qu\xc3\xadmica \xe2€•ou san Ant\xc3\xb3n\xe2€•: 21'
        self.assertEqual(tidy_title(raw), 'Reeducación química ―ou san Antón―: 21')

    def test_repair_rewrites_title_and_description(self):
        book = {'titulo': 'dERMATOLOGÍA GENERAL BÁSICA', 'descripcion_breve': 'dERMATOLOGÍA GENERAL BÁSICA, de Ana. Edición.'}
        self.assertEqual(q.repair_titles([book], ROOT, '2026-11-19'), 1)
        self.assertEqual(book['titulo'], 'Dermatología general básica')
        self.assertTrue(book['descripcion_breve'].startswith('Dermatología general básica, de Ana'))

    def test_clean_title_untouched(self):
        book = {'titulo': 'Cien años de soledad', 'descripcion_breve': 'Cien años de soledad, de G.'}
        self.assertEqual(q.repair_titles([book], ROOT, '2026-11-19'), 0)


if __name__ == '__main__':
    unittest.main()
