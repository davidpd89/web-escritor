import json
import re
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

class TopicPublicationGate(unittest.TestCase):
    def test_ready_and_draft_separation(self):
        data = json.loads((ROOT / 'data/topic-collections.json').read_text(encoding='utf-8'))
        collections = data['collections']
        ready = {x['slug'] for x in collections if x['status'] == 'ready'}
        draft = {x['slug'] for x in collections if x['status'] == 'draft'}
        self.assertTrue(ready)
        self.assertFalse(ready & draft)
        index = (ROOT / 'cuaderno/temas/index.html').read_text(encoding='utf-8')
        published = set(re.findall(r'/cuaderno/temas/([a-z0-9-]+)/', index))
        self.assertEqual(published, ready)
        feed = ET.parse(ROOT / 'cuaderno/feed.xml')
        feed_links = [n.text or '' for n in feed.findall('./channel/item/link')]
        for item in collections:
            slug = item['slug']
            path = ROOT / 'cuaderno/temas' / slug / 'index.html'
            if slug in ready:
                self.assertTrue(path.is_file(), slug)
                self.assertGreaterEqual(len(item['items']), 3, slug)
            else:
                self.assertFalse(path.exists(), f'Borrador publicado: {slug}')
                self.assertNotIn(f'/cuaderno/temas/{slug}/', index)
            self.assertFalse(any(f'/cuaderno/temas/{slug}/' in link for link in feed_links), slug)

if __name__ == '__main__':
    unittest.main()
