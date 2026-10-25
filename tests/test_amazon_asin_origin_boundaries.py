import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reading_amazon_market import asin_from_url

ASIN = 'B08CYCPBZN'

class AmazonAsinOriginTests(unittest.TestCase):
    def test_legitimate_products(self):
        for url in (
            f'https://www.amazon.es/dp/{ASIN}',
            f'https://amazon.es/gp/product/{ASIN}?tag=contrato-21',
        ):
            with self.subTest(url=url):
                self.assertEqual(asin_from_url(url), ASIN)

    def test_host_and_protocol_confusion(self):
        invalid = (
            f'https://amazon.es.evil.test/dp/{ASIN}',
            f'https://evil.test/amazon.es/dp/{ASIN}',
            f'https://www.amazon.es@evil.test/dp/{ASIN}',
            f'http://www.amazon.es/dp/{ASIN}',
            f'javascript:/dp/{ASIN}',
            f'//evil.test/dp/{ASIN}',
            f'https://evil.test/?next=/dp/{ASIN}',
        )
        for url in invalid:
            with self.subTest(url=url):
                self.assertIsNone(asin_from_url(url), url)

if __name__ == '__main__':
    unittest.main()
