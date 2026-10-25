import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reading_goodreads import GoodreadsPublic

class FakeResponse:
    def __init__(self, url):
        self.url = url
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, limit):
        return b'<html></html>'

class GoodreadsRedirectTests(unittest.TestCase):
    def test_secure_redirect_allowed(self):
        client = GoodreadsPublic(delay=0)
        with patch('reading_goodreads.urlopen', return_value=FakeResponse('https://www.goodreads.com/book/show/123')):
            text, final = client.fetch('https://www.goodreads.com/book/isbn/9788498382372')
        self.assertEqual(final, 'https://www.goodreads.com/book/show/123')

    def test_insecure_or_ambiguous_redirect_rejected(self):
        destinations = (
            'http://www.goodreads.com/book/show/123',
            'https://www.goodreads.com:8443/book/show/123',
            'https://user@www.goodreads.com/book/show/123',
            'https://www.goodreads.com.evil.test/book/show/123',
        )
        for destination in destinations:
            with self.subTest(destination=destination):
                client = GoodreadsPublic(delay=0)
                with patch('reading_goodreads.urlopen', return_value=FakeResponse(destination)):
                    with self.assertRaises(ValueError):
                        client.fetch('https://www.goodreads.com/book/isbn/9788498382372')

if __name__ == '__main__':
    unittest.main()
