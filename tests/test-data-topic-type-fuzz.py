import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/build-topic-collections.py'
SPEC = importlib.util.spec_from_file_location('topic_builder_qa', SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
BASE = json.loads((ROOT / 'data/topic-collections.json').read_text(encoding='utf-8'))

class TopicTypeFuzz(unittest.TestCase):
    def test_valid_baseline(self):
        self.assertTrue(MODULE.validate(copy.deepcopy(BASE)))

    def test_invalid_collection_shapes(self):
        for value in [None, False, 7, 'texto', {}, [1], ['texto']]:
            with self.subTest(value=value):
                payload = copy.deepcopy(BASE)
                payload['collections'] = value
                with self.assertRaises(MODULE.ValidationError):
                    MODULE.validate(payload)

    def test_invalid_record_shapes(self):
        for value in [None, False, 7, 'texto', [], ['texto']]:
            with self.subTest(value=value):
                payload = copy.deepcopy(BASE)
                payload['collections'][0] = value
                with self.assertRaises(MODULE.ValidationError):
                    MODULE.validate(payload)

    def test_invalid_item_shapes(self):
        for value in [None, False, 7, 'texto', [], ['texto']]:
            with self.subTest(value=value):
                payload = copy.deepcopy(BASE)
                payload['collections'][0]['items'][0] = value
                with self.assertRaises(MODULE.ValidationError):
                    MODULE.validate(payload)

    def test_invalid_items_container(self):
        for value in [None, False, 7, 'texto', {}, [None]]:
            with self.subTest(value=value):
                payload = copy.deepcopy(BASE)
                payload['collections'][0]['items'] = value
                with self.assertRaises(MODULE.ValidationError):
                    MODULE.validate(payload)

if __name__ == '__main__':
    unittest.main()
