from __future__ import annotations
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://davidportodiaz.com/'
class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonical = []
        self.og = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonical.append(attrs.get('href'))
        if tag == 'meta' and attrs.get('property') == 'og:url':
            self.og.append(attrs.get('content'))

pages = sorted((ROOT / 'editoriales').glob('*/index.html'))
assert pages
for page in pages:
    metadata = Metadata()
    metadata.feed(page.read_text(encoding='utf-8'))
    expected = BASE + page.parent.relative_to(ROOT).as_posix() + '/'
    assert metadata.canonical == [expected], f'{page}: canonical {metadata.canonical!r}'
    assert metadata.og == [expected], f'{page}: og:url {metadata.og!r}'
print(f'editoriales canonical/OG parity: OK ({len(pages)} páginas)')
