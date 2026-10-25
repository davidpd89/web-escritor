import unittest
from pathlib import Path
from urllib.parse import urlsplit, unquote
import xml.etree.ElementTree as ET
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MEDIA = '{http://search.yahoo.com/mrss/}content'
MIME = {'JPEG': 'image/jpeg', 'PNG': 'image/png', 'WEBP': 'image/webp'}

class PublishedFeedMediaBinary(unittest.TestCase):
    def test_real_image_format(self):
        feeds = sorted((ROOT / 'assets/pinterest/feeds').glob('*.xml'))
        self.assertTrue(feeds, 'No hay feeds RSS publicados')
        for feed in feeds:
            for item in ET.parse(feed).findall('./channel/item'):
                media = item.find(MEDIA)
                self.assertIsNotNone(media, f'{feed}: elemento sin imagen')
                url = media.get('url', '')
                parsed = urlsplit(url)
                with self.subTest(feed=feed.name, image=url):
                    self.assertEqual(parsed.netloc, 'davidportodiaz.com', f'{feed}: origen {url}')
                    relative = unquote(parsed.path).lstrip('/')
                    path = (ROOT / relative).resolve()
                    self.assertTrue(path.is_relative_to((ROOT / 'assets').resolve()), f'{feed}: ruta insegura {url}')
                    self.assertTrue(path.is_file(), f'{feed}: archivo ausente {url}')
                    with Image.open(path) as image:
                        actual = MIME.get(image.format)
                        self.assertIsNotNone(actual, f'{feed}: formato no permitido {image.format} en {url}')
                        self.assertEqual(media.get('type'), actual, f'{feed}: MIME incorrecto para {url}')
                        image.verify()

if __name__ == '__main__':
    unittest.main()
