import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feed_under_test', ROOT / 'scripts/build-feed.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class FeedCollectionExclusion(unittest.TestCase):
    def test_flat_collection_is_not_article(self):
        document = {'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': 'Temas'}
        self.assertTrue(mod.is_non_article_page(document))

    def test_graph_collection_is_not_article(self):
        document = {'@graph': [{'@type': 'CollectionPage', 'name': 'Temas'}]}
        self.assertTrue(mod.is_non_article_page(document))

    def test_article_graph_remains_eligible(self):
        document = {'@graph': [{'@type': 'CollectionPage'}, {'@type': 'Article'}]}
        self.assertFalse(mod.is_non_article_page(document))

if __name__ == '__main__':
    unittest.main()