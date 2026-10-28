import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reading_goodreads import StructuredBook

class NestedJsonLd(unittest.TestCase):
    def parse(self, payload):
        parser = StructuredBook()
        parser.feed('<script type="application/ld+json">' + json.dumps(payload) + '</script>')
        return parser.books

    def test_list_containing_graph(self):
        book = {'@type': 'Book', 'name': 'Coraline', 'isbn': '9788498382372'}
        payload = [{'@context': 'https://schema.org', '@graph': [{'@type': 'WebPage'}, book]}]
        self.assertEqual(self.parse(payload), [book])

    def test_graph_with_unrelated_nodes(self):
        book = {'@type': 'Book', 'name': 'Coraline'}
        payload = {'@graph': [{'@type': 'Organization'}, book, {'@type': 'Person'}]}
        self.assertEqual(self.parse(payload), [book])

if __name__ == '__main__':
    unittest.main()
