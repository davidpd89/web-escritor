import importlib.util
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('topic_editorial_parity', ROOT / 'scripts/build-topic-collections.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def visible_text(document):
    parser = VisibleText()
    parser.feed(document)
    return ' '.join(' '.join(parser.parts).split())


class TopicEditorialContentParity(unittest.TestCase):
    def test_published_collection_preserves_editorial_copy(self):
        data = json.loads((ROOT / 'data/topic-collections.json').read_text(encoding='utf-8'))
        collections = MODULE.validate(data)
        ready = [c for c in collections if c['status'] == 'ready']
        self.assertTrue(ready, 'data/topic-collections.json: no hay colecciones ready para comprobar')
        for collection in ready:
            with self.subTest(collection=collection['slug']):
                document = MODULE.render_hub(collection)
                text = visible_text(document)
                for field in ('title', 'intro'):
                    expected = ' '.join(collection[field].split())
                    self.assertIn(expected, text, f'/cuaderno/temas/{collection["slug"]}/: falta {field}: {expected!r}')
                for item in collection['items']:
                    for field in ('title', 'description'):
                        expected = ' '.join(item[field].split())
                        self.assertIn(expected, text, f'/cuaderno/temas/{collection["slug"]}/: {item["url"]} pierde {field}: {expected!r}')
                    self.assertIn(item['url'], document, f'/cuaderno/temas/{collection["slug"]}/: falta enlace a {item["url"]}')


if __name__ == '__main__':
    unittest.main()
