from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://davidportodiaz.com'
NS = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}


class HeadParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonical = []
        self.robots = []
        self.in_head = False

    def handle_starttag(self, tag, attrs):
        if tag == 'head':
            self.in_head = True
        if not self.in_head:
            return
        attrs = dict(attrs)
        if tag == 'link' and 'canonical' in (attrs.get('rel') or '').lower().split():
            self.canonical.append(attrs.get('href'))
        if tag == 'meta' and (attrs.get('name') or '').lower() == 'robots':
            self.robots.append(attrs.get('content') or '')

    def handle_endtag(self, tag):
        if tag == 'head':
            self.in_head = False


def check():
    xml = ET.parse(ROOT / 'sitemap.xml')
    errors = []
    for loc in xml.findall('.//s:loc', NS):
        url = loc.text or ''
        parts = urlsplit(url)
        if parts.scheme != 'https' or parts.netloc != 'davidportodiaz.com':
            errors.append(f'Origen no canónico: {url}')
            continue
        relative = unquote(parts.path).lstrip('/')
        target = ROOT / relative
        if parts.path.endswith('/'):
            target = target / 'index.html'
        if not target.is_file():
            errors.append(f'HTML inexistente: {url}')
            continue
        parser = HeadParser()
        parser.feed(target.read_text(encoding='utf-8'))
        if parser.canonical != [url]:
            errors.append(f'Canonical distinto: {url}: {parser.canonical}')
        if any('noindex' in value.lower().split(',') or 'noindex' in value.lower().split() for value in parser.robots):
            errors.append(f'Página noindex incluida: {url}')
    assert not errors, '\n'.join(errors)


if __name__ == '__main__':
    check()
    print('PASS sitemap HTML canonical parity')