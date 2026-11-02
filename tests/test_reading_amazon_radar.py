"""Radar de cobertura de Amazon: cifras agregadas, sin datos de producto y sin llamadas reales."""
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reading_amazon_radar import connected_publishers, coverage, radar_request, radar_rows, run

TODAY = date(2026, 11, 2)
CATALOGUE = {'libros': [{'isbn13': '9788439741008', 'editorial': 'Lumen', 'editorial_slug': 'penguin-es'}]}
ALIASES = [{'slug': 'penguin-es', 'aliases': ['Penguin Random House Grupo Editorial', 'Alfaguara']},
           {'slug': 'planeta-es', 'aliases': ['Destino']}]


def item(ean, publisher, published):
    return {'asin': 'B0X', 'itemInfo': {'externalIds': {'eans': {'displayValues': [ean]}},
                                        'byLineInfo': {'manufacturer': {'displayValue': publisher}},
                                        'contentInfo': {'publicationDate': {'displayValue': published}},
                                        'title': {'displayValue': 'No debe salir'}}}


PAGE = {'searchResult': {'items': [
    item('9788439741008', 'Lumen', '2026-10-01T00:00:01Z'),
    item('9788420000008', 'Alfaguara', '2026-12-01'),
    item('9788423300006', 'Destino', '2026-12-15'),
    item('9788433900005', 'Anagrama', '2026-09-01'),
    item('4012345678901', 'Juguetes', '2026-09-01'),
]}}


class Provider:
    def __init__(self, pages):
        self.pages, self.calls = pages, []

    def headers(self):
        return {}

    def post(self, url, payload, headers):
        self.calls.append(payload)
        return self.pages[len(self.calls) - 1]


class RadarTest(unittest.TestCase):
    def test_request_is_books_newest_first(self):
        request = radar_request('tag-21', 3)
        self.assertEqual((request['searchIndex'], request['sortBy'], request['itemPage']), ('Books', 'NewestArrivals', 3))
        for tag, page in (('mal tag', 1), ('tag-21', 0), ('tag-21', 11)):
            with self.assertRaises(ValueError):
                radar_request(tag, page)

    def test_rows_keep_only_isbn_publisher_and_date(self):
        rows = radar_rows(PAGE)
        self.assertEqual(len(rows), 4)  # el EAN que no es libro queda fuera
        self.assertEqual(rows[0], {'isbn13': '9788439741008', 'editorial': 'Lumen', 'fecha': '2026-10-01'})
        self.assertEqual(radar_rows({'searchResult': None}), [])

    def test_connected_includes_aliases_of_live_connectors_only(self):
        connected = connected_publishers(CATALOGUE, ALIASES)
        self.assertIn('alfaguara', connected)
        self.assertNotIn('destino', connected)

    def test_coverage_counts_missing_and_unconnected(self):
        report = coverage(radar_rows(PAGE), CATALOGUE, connected_publishers(CATALOGUE, ALIASES), TODAY)
        self.assertEqual(report['resultados'], 4)
        self.assertEqual(report['en_catalogo'], 1)
        self.assertEqual(report['faltan'], 3)
        self.assertEqual(report['faltan_proximamente'], 2)
        self.assertEqual(report['faltan_con_conector'], 1)
        self.assertEqual(report['editoriales_sin_conector'], {'Destino': 1, 'Anagrama': 1})
        self.assertNotIn('No debe salir', str(report))

    def test_run_stops_on_short_page(self):
        provider = Provider([{'searchResult': {'items': [item('9788420000008', 'Alfaguara', '2026-12-01')] * 10}}, PAGE, PAGE])
        report = run(provider, CATALOGUE, ALIASES, 'tag-21', today=TODAY, pages=10)
        self.assertEqual(report['peticiones'], 2)
        self.assertEqual([c['itemPage'] for c in provider.calls], [1, 2])


if __name__ == '__main__':
    unittest.main()
