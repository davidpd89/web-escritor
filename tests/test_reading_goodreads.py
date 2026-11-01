"""Identity, stale-data and stop-on-denial contracts for public aggregates."""
import copy
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reading_goodreads import GoodreadsPublic, StructuredBook, select_goodreads_rating
from reading_ratings_refresh import refresh

BOOK = {'id': 'lib-0001', 'isbn13': '9788498382372', 'titulo': 'Coraline',
        'autores': ['Neil Gaiman'], 'estado': 'publicado'}
RESPONSE = {'url': 'https://www.goodreads.com/book/show/6785288-coraline', 'books': [{
    '@type': 'Book', 'isbn': '9788498382372', 'name': 'Coraline',
    'author': [{'name': 'Neil Gaiman'}, {'name': 'Traductora'}],
    'aggregateRating': {'ratingValue': '4.13', 'ratingCount': '809434'}}]}


class GoodreadsTests(unittest.TestCase):
    def test_matching_edition_only(self):
        rated = select_goodreads_rating(BOOK, RESPONSE)
        self.assertEqual((rated['fuente'], rated['puntuacion'], rated['numero_valoraciones']),
                         ('goodreads', 4.13, 809434))
        for field, value in [('isbn', '9788425374012'), ('name', 'Otro libro'),
                             ('author', [{'name': 'Otro autor'}])]:
            wrong = copy.deepcopy(RESPONSE)
            wrong['books'][0][field] = value
            self.assertIsNone(select_goodreads_rating(BOOK, wrong))

    def test_bad_votes_or_links_never_publish(self):
        for count in [True, 0, -1, 1.5, 'desconocido']:
            wrong = copy.deepcopy(RESPONSE)
            wrong['books'][0]['aggregateRating']['ratingCount'] = count
            self.assertIsNone(select_goodreads_rating(BOOK, wrong))
        for url in ['https://evil.example/book/show/1',
                    'https://www.goodreads.com:443/book/show/1',
                    'https://www.goodreads.com/book/show/1?token=secret']:
            self.assertIsNone(select_goodreads_rating(BOOK, dict(RESPONSE, url=url)))

    def test_legacy_rating_preserved_on_failure_without_fake_freshness(self):
        old = {'libro_id': BOOK['id'], 'puntuacion': 4.1, 'numero_valoraciones': 10,
               'url': RESPONSE['url'], 'actualizado_en': '2026-10-20T00:00:00Z'}
        def unavailable(isbn):
            raise RuntimeError('provider unavailable')
        market, stats = refresh({'libros': [BOOK]}, {'ratings': [old], 'offers': []},
                                unavailable, now=datetime(2026, 10, 21, tzinfo=timezone.utc),
                                budget=100, source='goodreads')
        self.assertEqual(market['ratings'], [old])
        self.assertEqual(stats['updated'], 0)
        self.assertEqual(len(stats['failures']), 1)

    def test_denial_stops_all_following_requests(self):
        provider = GoodreadsPublic(delay=0)
        with patch.object(provider, 'fetch', side_effect=HTTPError(
                'https://www.goodreads.com/robots.txt', 429, 'limited', {}, None)) as fetch:
            for _ in range(2):
                with self.assertRaises(RuntimeError):
                    provider(BOOK['isbn13'])
            self.assertEqual(fetch.call_count, 1)

    def test_refresh_stops_unavailable_source_without_exhausting_budget(self):
        other = dict(BOOK, id='lib-0002', isbn13='9788425374012')
        with patch('builtins.print'):
            calls = []
            def unavailable(isbn):
                calls.append(isbn)
                raise RuntimeError('HTTP 503')
            _, stats = refresh({'libros': [BOOK, other]}, {'ratings': [], 'offers': []},
                               unavailable, now=datetime(2026, 10, 21, tzinfo=timezone.utc),
                               budget=100, source='google_books')
        self.assertEqual(len(calls), 1)
        self.assertTrue(stats['stopped'])
        self.assertEqual(stats['attempted'], 1)

    def test_transliterated_author_matches_only_with_exact_isbn_and_title(self):
        alias = copy.deepcopy(RESPONSE)
        alias['books'][0]['author'] = [{'name': 'Neil Gaimann'}]
        self.assertEqual(select_goodreads_rating(BOOK, alias)['numero_valoraciones'], 809434)
        for author in ['Neil', 'Gaiman Neil Smith', 'Nora Gaitan']:
            alias['books'][0]['author'] = [{'name': author}]
            self.assertIsNone(select_goodreads_rating(BOOK, alias), author)

    def test_book_page_without_structured_data_is_a_failure_not_unrated(self):
        import json
        page = ('<script type="application/ld+json">' + json.dumps(RESPONSE['books'][0]) + '</script>', RESPONSE['url'])
        degraded = ('<html><div id="__next"></div></html>', RESPONSE['url'])
        provider = GoodreadsPublic(delay=0, backoff=(0,))
        provider.robots = __import__('urllib.robotparser').robotparser.RobotFileParser(); provider.robots.parse([])
        with patch.object(provider, 'fetch', side_effect=[degraded, page]):
            self.assertEqual(provider(BOOK['isbn13'])['books'], RESPONSE['books'])
        with patch.object(provider, 'fetch', return_value=degraded):
            for _ in range(provider.MAX_DEGRADED - 1):
                with self.assertRaises(ValueError):
                    provider(BOOK['isbn13'])
            with self.assertRaises(RuntimeError):
                provider(BOOK['isbn13'])
        missing = GoodreadsPublic(delay=0, backoff=(0,)); missing.robots = provider.robots
        with patch.object(missing, 'fetch', return_value=('<html></html>', 'https://www.goodreads.com/search?q=1')):
            self.assertEqual(missing(BOOK['isbn13'])['books'], [])
        old = {'libro_id': BOOK['id'], 'fuente': 'goodreads', 'puntuacion': 4.1, 'numero_valoraciones': 9, 'url': RESPONSE['url'],
               'actualizado_en': '2026-09-01T00:00:00Z', 'caduca_en': '2026-10-01T00:00:00Z'}
        broken = GoodreadsPublic(delay=0, backoff=(0,)); broken.robots = provider.robots
        books = [dict(BOOK, id=f'lib-{i}') for i in range(5)]
        with patch.object(broken, 'fetch', return_value=degraded):
            result, stats = refresh({'libros': [BOOK, *books]}, {'ratings': [old], 'offers': []}, broken,
                                    now=datetime(2026, 10, 21, tzinfo=timezone.utc), budget=10, source='goodreads')
        self.assertEqual((stats['unrated'], len(stats['failures']), stats.get('stopped')), (0, broken.MAX_DEGRADED, True))
        self.assertEqual(result['ratings'], [old])

    def test_aws_waf_challenge_stops_the_provider_on_first_sight(self):
        class Challenge:
            url, status = RESPONSE['url'], 202
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, n): return b'<script>window.awsWafCookieDomainList = [];window.gokuProps = {}</script>'
        provider = GoodreadsPublic(delay=0, backoff=(0,))
        provider.robots = __import__('urllib.robotparser').robotparser.RobotFileParser(); provider.robots.parse([])
        with patch('reading_goodreads.urlopen', return_value=Challenge()) as transport:
            with self.assertRaisesRegex(RuntimeError, 'WAF'):
                provider(BOOK['isbn13'])
            with self.assertRaises(RuntimeError):
                provider(BOOK['isbn13'])
        self.assertEqual(transport.call_count, 1)
        self.assertEqual(provider.degraded, 0)

    def test_invalid_isbn_never_requests(self):
        provider = GoodreadsPublic(delay=0)
        with patch.object(provider, 'fetch') as fetch:
            with self.assertRaises(ValueError):
                provider('../../search')
            fetch.assert_not_called()

    def test_parser_rejects_broken_json_and_handles_graph(self):
        import json
        parser = StructuredBook()
        parser.feed('<script type="application/ld+json">broken</script>')
        parser.feed('<script type="application/ld+json">' + json.dumps(
            {'@graph': RESPONSE['books']}) + '</script>')
        self.assertEqual(parser.books, RESPONSE['books'])


if __name__ == '__main__':
    unittest.main()
