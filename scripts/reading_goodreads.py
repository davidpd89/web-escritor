"""Public ISBN pages only; no search crawling, login, reviews or bot bypass."""
import json
import math
import re
import time
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
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
                def collect_books(node):
                    if isinstance(node, list):
                        for child in node:
                            collect_books(child)
                    elif isinstance(node, dict):
                        types = node.get('@type')
                        if types == 'Book' or (isinstance(types, list) and 'Book' in types):
                            self.books.append(node)
                        graph = node.get('@graph')
                        if isinstance(graph, (list, dict)):
                            collect_books(graph)

                collect_books(item)
            except (ValueError, TypeError, AttributeError): pass

def same_author(source, catalogued):
    """Con ISBN y título ya exactos, admite transliteraciones (Alaa El Aswany / Alaa al Aswani), nunca otro nombre."""
    from difflib import SequenceMatcher
    from reading_ratings_refresh import author_matches, key
    a, b = key(source), key(catalogued)
    return author_matches(source, catalogued) or (
        len(a.split()) == len(b.split()) >= 2 and SequenceMatcher(None, a, b).ratio() >= 0.8)

def select_goodreads_rating(book, response):
    from reading_ratings_refresh import isbn13, title_matches
    wanted = isbn13(book.get('isbn13', ''))
    if not wanted:
        return None
    for obj in response.get('books', []):
        if not isinstance(obj, dict): continue
        if isbn13(str(obj.get('isbn', ''))) != wanted: continue
        if not title_matches(str(obj.get('name', '')), book['titulo']): continue
        authors = obj.get('author', []); authors = authors if isinstance(authors, list) else [authors]
        if not any(same_author(str(a.get('name', '')), name) for a in authors if isinstance(a, dict) for name in book['autores']): continue
        rating = obj.get('aggregateRating')
        if not isinstance(rating, dict): continue
        value = rating.get('ratingValue'); count = rating.get('ratingCount')
        if isinstance(value, bool) or isinstance(count, bool): continue
        try:
            value, parsed_count = float(value), float(count)
            if not math.isfinite(value) or not math.isfinite(parsed_count):
                continue
            count = int(parsed_count)
        except (ValueError, TypeError): continue
        if count != parsed_count: continue
        url = response.get('url', ''); parsed = urlsplit(url)
        if parsed.scheme != 'https' or parsed.netloc != 'www.goodreads.com' or parsed.query or parsed.fragment or not re.fullmatch(r'/book/show/\d+[A-Za-z0-9_.-]*', parsed.path): continue
        if 1 <= value <= 5 and count > 0:
            return {'libro_id': book['id'], 'puntuacion': value, 'numero_valoraciones': count, 'fuente': 'goodreads', 'url': url}
    return None

class DegradedPage(ValueError):
    """Book page served without its Book JSON-LD: a failure for that ISBN, never an unrated book."""

class GoodreadsPublic:
    MAX_DEGRADED = 3  # consecutive degraded pages before the provider is considered blocked for the run
    def __init__(self, delay=2, backoff=(20, 60)):
        self.delay = delay; self.backoff = backoff; self.last = 0; self.robots = None; self.unavailable = False; self.degraded = 0
    def fetch(self, url):
        # Goodreads answers sporadic 503/429 bursts; wait and retry before giving up the run.
        for pause in (*self.backoff, None):
            try:
                return self.fetch_once(url)
            except (HTTPError, URLError, TimeoutError) as exc:
                if pause is None or getattr(exc, 'code', 503) not in (429, 503): raise
                time.sleep(pause)
    def fetch_once(self, url):
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
            text = raw.decode('utf-8')
            # AWS WAF answers 202 with a JS challenge instead of the page: the run is blocked, not the book.
            if getattr(response, 'status', 200) == 202 or 'awsWafCookieDomainList' in text:
                raise RuntimeError('Goodreads AWS WAF challenge')
            return text, response.url
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
            for pause in (*self.backoff[:1], None):
                text, final = self.fetch(url)
                if not self.robots.can_fetch(AGENT, final): raise RuntimeError('Goodreads robots disallows destination')
                parser = StructuredBook(); parser.feed(text)
                # A book page always carries its Book JSON-LD; without it the page is degraded, not unrated.
                if parser.books or not urlsplit(final).path.startswith('/book/show/'):
                    self.degraded = 0
                    return {'books': parser.books, 'url': final}
                if pause is not None: time.sleep(pause)
            self.degraded += 1
            if self.degraded >= self.MAX_DEGRADED:
                raise RuntimeError(f'{self.degraded} consecutive degraded book pages')
            raise DegradedPage('Goodreads book page without structured data')
        except DegradedPage:
            raise
        except Exception as exc:
            # A missing ISBN is ordinary; denial/rate limit/transport failure stops the provider.
            if getattr(exc, 'code', None) == 404: return {'books': []}
            self.unavailable = True
            raise RuntimeError('Goodreads public lookup failed: ' + type(exc).__name__ + (' ' + str(exc)[:80] if isinstance(exc, (ValueError, RuntimeError)) else '') + (' ' + str(getattr(exc, 'code', '')) if getattr(exc, 'code', None) else '')) from exc
