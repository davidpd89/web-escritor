import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class LD(HTMLParser):
    def __init__(self):
        super().__init__()
        self.on = False
        self.buf = []
        self.docs = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('type') == 'application/ld+json':
            self.on = True
            self.buf = []

    def handle_data(self, text):
        if self.on:
            self.buf.append(text)

    def handle_endtag(self, tag):
        if tag == 'script' and self.on:
            self.docs.append(json.loads(''.join(self.buf)))
            self.on = False

rows = json.loads((ROOT / 'data/editoriales.json').read_text(encoding='utf-8'))['publishers']
for r in (x for x in rows if x.get('publish')):
    html = (ROOT / 'editoriales' / r['slug'] / 'index.html').read_text(encoding='utf-8')
    p = LD()
    p.feed(html)
    pages = [node for doc in p.docs for node in doc.get('@graph', [doc])
             if node.get('@type') == 'WebPage']
    assert len(pages) == 1 and pages[0]['dateModified'] == r['page_updated_at'], r['slug']
    beginning = html.index('Historial de comprobaciones y cambios')
    ending = html.index('>Fuentes<', beginning)
    block = html[beginning:ending]
    observed = re.findall(r'<time datetime="(\d{4}-\d{2}-\d{2})"', block)
    expected = sorted((event['date'] for event in r['history']), reverse=True)
    assert observed == expected, (r['slug'], observed, expected)
print('editorial history parity: OK')
