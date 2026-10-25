import unittest
from pathlib import Path
from urllib.parse import urlsplit, unquote
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = '{http://search.yahoo.com/mrss/}content'

class PublishedFeedMediaOrigin(unittest.TestCase):
    def test_media_origins(self):
        feeds = sorted((ROOT / 'assets/pinterest/feeds').glob('*.xml'))
        self.assertTrue(feeds, 'No existen feeds publicados para comprobar')
        for feed in feeds:
            for item in ET.parse(feed).findall('./channel/item'):
                media = item.find(NS)
                with self.subTest(feed=feed.name, title=item.findtext('title')):
                    self.assertIsNotNone(media, f'{feed}: item sin media:content')
                    url = media.get('url', '')
                    parsed = urlsplit(url)
                    self.assertEqual((parsed.scheme, parsed.netloc), ('https', 'davidportodiaz.com'), f'{feed}: origen multimedia {url}')
                    self.assertFalse(parsed.query or parsed.fragment, f'{feed}: URL multimedia no canónica {url}')
                    relative = unquote(parsed.path).lstrip('/')
                    self.assertTrue(relative.startswith('assets/'), f'{feed}: imagen fuera de assets: {url}')
                    target = (ROOT / relative).resolve()
                    self.assertTrue(target.is_relative_to((ROOT / 'assets').resolve()), f'{feed}: ruta multimedia fuera de assets: {url}')
                    self.assertTrue(target.is_file(), f'{feed}: imagen inexistente: {url}')

if __name__ == '__main__':
    unittest.main()
