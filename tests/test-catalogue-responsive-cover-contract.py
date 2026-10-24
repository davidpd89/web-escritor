from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class Covers(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cards = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'li' and 'data-catalogue-book' in a:
            self.current = {'id': a.get('data-book-id'), 'image': None}
            self.cards.append(self.current)
        elif tag == 'img' and self.current is not None:
            if 'catalogue-book-cover' in (a.get('class') or '').split():
                self.current['image'] = a

class CoverContract(unittest.TestCase):
    def test_real_responsive_images_and_reserved_space(self):
        p = Covers()
        p.feed((ROOT / 'recomendaciones/index.html').read_text(encoding='utf-8'))
        self.assertGreater(len(p.cards), 50)
        for index, card in enumerate(p.cards):
            with self.subTest(book=card['id']):
                image = card['image']
                self.assertIsNotNone(image, 'Falta la portada')
                self.assertTrue((image.get('alt') or '').strip())
                self.assertGreater(int(image.get('width') or 0), 0)
                self.assertGreater(int(image.get('height') or 0), 0)
                self.assertTrue(image.get('sizes'))
                self.assertTrue(image.get('srcset'))
                sources = [part.strip().split()[0] for part in image['srcset'].split(',')]
                for source in [image['src'], *sources]:
                    self.assertTrue(source.startswith('/assets/reading-covers/'), source)
                    self.assertTrue((ROOT / source.lstrip('/')).is_file(), source)
                if index >= 2:
                    self.assertEqual(image.get('loading'), 'lazy', 'Portada posterior al bloque inicial cargada inmediatamente')

if __name__ == '__main__':
    unittest.main()