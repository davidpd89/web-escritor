import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from reading_goodreads import GoodreadsPublic

class Response:
    def __init__(self,url,data=b'<html></html>'):
        self.url=url
        self.data=data
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self,n): return self.data[:n]

class TransportBoundaries(unittest.TestCase):
    def test_redirect_keeps_https_and_public_origin(self):
        for final in [
            'http://www.goodreads.com/book/show/123',
            'https://usuario@www.goodreads.com/book/show/123',
            'https://www.goodreads.com:8443/book/show/123',
            'https://www.goodreads.com.evil.test/book/show/123'
        ]:
            with self.subTest(final=final):
                with patch('reading_goodreads.urlopen',return_value=Response(final)):
                    with self.assertRaises(ValueError):
                        GoodreadsPublic(delay=0).fetch('https://www.goodreads.com/book/isbn/9788498382372')
    def test_response_limit_does_not_allow_more_than_three_megabytes(self):
        payload=b'x'*3000001
        with patch('reading_goodreads.urlopen',return_value=Response('https://www.goodreads.com/book/show/123',payload)):
            with self.assertRaises(ValueError):
                GoodreadsPublic(delay=0).fetch('https://www.goodreads.com/book/isbn/9788498382372')

if __name__=='__main__': unittest.main()
