from html.parser import HTMLParser
from pathlib import Path

PAGE = Path(__file__).resolve().parents[1] / 'publicar-web/index.html'

class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.current = None
        self.ids = {}
        self.capture = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.capture.append((tag, a['id'], []))
        if tag == 'a':
            self.current = {'href': a.get('href', ''), 'label': a.get('aria-label', ''), 'labelledby': a.get('aria-labelledby', ''), 'text': [], 'images': []}
        if tag == 'img' and self.current is not None:
            self.current['images'].append(a.get('alt'))

    def handle_data(self, data):
        if self.current is not None:
            self.current['text'].append(data)
        for _, _, parts in self.capture:
            parts.append(data)

    def handle_endtag(self, tag):
        if self.capture and self.capture[-1][0] == tag:
            _, key, parts = self.capture.pop()
            self.ids[key] = ''.join(parts).strip()
        if tag == 'a' and self.current is not None:
            self.links.append(self.current)
            self.current = None

p = Links()
p.feed(PAGE.read_text(encoding='utf-8'))
assert p.links, f'{PAGE}: ningún enlace encontrado'
for link in p.links:
    refs = link['labelledby'].split()
    if refs:
        for ref in refs:
            assert ref in p.ids, f'{PAGE}: enlace {link["href"]} referencia ID inexistente {ref}'
    referenced = ' '.join(p.ids.get(ref, '') for ref in refs)
    text = ''.join(link['text']).strip()
    image_text = ' '.join(alt for alt in link['images'] if alt)
    name = (referenced if refs else link['label'] or (text + ' ' + image_text)).strip()
    assert name, f'{PAGE}: enlace {link["href"]} sin nombre accesible'
    assert any(c.isalnum() for c in name), f'{PAGE}: enlace {link["href"]} con nombre no descriptivo {name!r}'
print(f'OK {PAGE}: {len(p.links)} enlaces con nombres accesibles')