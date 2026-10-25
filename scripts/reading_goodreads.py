"""Public ISBN pages only; no search crawling, login, reviews or bot bypass."""
import json
import re
import time
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

AGENT = 'DavidPortoReadingCatalogue/1.0 (+https://davidportodiaz.com)'

class StructuredBook(HTMLParser):
    def __init__(self):
        super().__init__(); self.capture = False; self.parts = []; self.books = []
    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('type') == 'application/ld+json':
            self.capture = True; self.parts = []
    def handle_data(self, value):
        if self.capture: self.parts.append(value)
    def handle_endtag(self, tag):
        if tag == 'script' and self.capture:
            self.capture = False
            try:
                item = json.loads(''.join(self.parts))
                for obj in item if isinstance(item, list) else item.get('@graph', [item]):
                    if isinstance(obj, dict):
                        types = obj.get('@type')
                        if types == 'Book' or (isinstance(types, list) and 'Book' in types):
                            self.books.append(obj)
            except (ValueError, TypeError, AttributeError): pass

def select_goodreads_rating(book, response):
    from reading_ratings_refresh import isbn13, title_matches, author_matches
    wanted = isbn13(book.get('isbn13', ''))
    if not wanted:
        return None
    for obj in response.get('books', []):
        if not isinstance(obj, dict): continue
        if isbn13(str(obj.get('isbn', ''))) != wanted: continue
        if not title_matches(str(obj.get('name', '')), book['titulo']): continue
        authors = obj.get('author', []); authors = authors if isinstance(authors, list) else [authors]
        if not any(author_matches(str(a.get('name', '')), name) for a in authors if isinstance(a, dict) for name in book['autores']): continue
        rating = obj.get('aggregateRating')
        if not isinstance(rating, dict): continue
        value = rating.get('ratingValue'); count = rating.get('ratingCount')
        if isinstance(value, bool) or isinstance(count, bool): continue
        try:
            value, parsed_count = float(value), float(count)
            count = int(parsed_count)
        except (ValueError, TypeError): continue
        if count != parsed_count: continue
        url = response.get('url', ''); parsed = urlsplit(url)
        if parsed.scheme != 'https' or parsed.netloc != 'www.goodreads.com' or parsed.query or parsed.fragment or not re.fullmatch(r'/book/show/\d+[A-Za-z0-9_.-]*', parsed.path): continue
        if 1 <= value <= 5 and count > 0:
            return {'libro_id': book['id'], 'puntuacion': value, 'numero_valoraciones': count, 'fuente': 'goodreads', 'url': url}
    return None

class GoodreadsPublic:
    def __init__(self, delay=2):
        self.delay = delay; self.last = 0; self.robots = None; self.unavailable = False
    def fetch(self, url):
        time.sleep(max(0, self.delay - (time.monotonic() - self.last))); self.last = time.monotonic()
        with urlopen(Request(url, headers={'User-Agent': AGENT, 'Accept': 'text/html'}), timeout=18) as response:
            final_url = urlsplit(response.url)
            if (final_url.scheme != 'https'
                    or final_url.hostname != 'www.goodreads.com'
                    or final_url.username is not None
                    or final_url.password is not None
                    or final_url.port not in (None, 443)):
                raise ValueError('Unexpected Goodreads redirect')
            raw = response.read(3_000_001)
            if len(raw) > 3_000_000: raise ValueError('Goodreads response too large')
            return raw.decode('utf-8'), response.url
    def __call__(self, isbn):
        from reading_ratings_refresh import isbn13
        isbn = isbn13(isbn)
        if not isbn:
            raise ValueError('Invalid ISBN; no request made')
        if self.unavailable: raise RuntimeError('Goodreads unavailable for this run; no further requests')
        try:
            if self.robots is None:
                text, _ = self.fetch('https://www.goodreads.com/robots.txt')
                self.robots = RobotFileParser(); self.robots.parse(text.splitlines())
            url = 'https://www.goodreads.com/book/isbn/' + isbn
            if not self.robots.can_fetch(AGENT, url): raise RuntimeError('Goodreads robots disallows ISBN lookup')
            text, final = self.fetch(url)
            if not self.robots.can_fetch(AGENT, final): raise RuntimeError('Goodreads robots disallows destination')
            parser = StructuredBook(); parser.feed(text)
            return {'books': parser.books, 'url': final}
        except Exception as exc:
            # A missing ISBN is ordinary; denial/rate limit/transport failure stops the provider.
            if getattr(exc, 'code', None) == 404: return {'books': []}
            self.unavailable = True
            raise RuntimeError('Goodreads public lookup failed: ' + type(exc).__name__) from exc
