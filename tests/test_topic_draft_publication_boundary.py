import importlib.util
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('topic_draft_boundary', ROOT / 'scripts/build-topic-collections.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


class TopicDraftPublicationBoundary(unittest.TestCase):
    def test_index_respects_real_editorial_status(self):
        data = json.loads((ROOT / 'data/topic-collections.json').read_text(encoding='utf-8'))
        collections = MODULE.validate(data)
        ready = [c for c in collections if c['status'] == 'ready']
        drafts = [c for c in collections if c['status'] == 'draft']
        self.assertTrue(ready, 'data/topic-collections.json: falta la colección publicada de control')
        self.assertTrue(drafts, 'data/topic-collections.json: falta la serie en borrador de control')
        document = MODULE.render_index(ready)
        parser = TextParser()
        parser.feed(document)
        text = ' '.join(' '.join(parser.parts).split())
        for collection in ready:
            with self.subTest(published=collection['slug']):
                self.assertIn(collection['title'], text, f'/cuaderno/temas/: falta colección publicada {collection["slug"]}')
                self.assertIn('/cuaderno/temas/' + collection['slug'] + '/', document, f'/cuaderno/temas/: falta destino publicado {collection["slug"]}')
        for collection in drafts:
            with self.subTest(draft=collection['slug']):
                self.assertNotIn(collection['title'], text, f'/cuaderno/temas/: se anuncia el borrador {collection["slug"]}')
                self.assertNotIn('/cuaderno/temas/' + collection['slug'] + '/', document, f'/cuaderno/temas/: se enlaza una serie no publicada: {collection["slug"]}')


if __name__ == '__main__':
    unittest.main()
