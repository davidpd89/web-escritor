from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, parse_qs

ROOT = Path(__file__).resolve().parents[1]

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.styles = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'link' and 'stylesheet' in a.get('rel', '').lower().split():
            self.styles.append(a.get('href', ''))

page = ROOT / 'lecturas/index.html'
p = Links()
p.feed(page.read_text(encoding='utf-8'))
assert p.styles, 'lecturas/index.html: no hay hojas de estilo'
seen = set()
for href in p.styles:
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc:
        continue
    assert parsed.path.startswith('/'), f'lecturas/index.html: CSS no absoluto {href}'
    assert parsed.path not in seen, f'lecturas/index.html: CSS duplicado {href}'
    seen.add(parsed.path)
    assert parsed.path.endswith('.css'), f'lecturas/index.html: stylesheet no CSS {href}'
    params = parse_qs(parsed.query, keep_blank_values=True)
    if 'v' in params:
        assert len(params['v']) == 1 and params['v'][0].strip(), f'lecturas/index.html: versión vacía {href}'
    asset = ROOT / parsed.path.lstrip('/')
    assert asset.is_file(), f'lecturas/index.html: CSS inexistente {href}'
    css = asset.read_text(encoding='utf-8')
    assert css.strip(), f'lecturas/index.html: CSS vacío {href}'
assert '/assets/reading-list.css' in seen, 'lecturas/index.html: falta la hoja de estilo de lecturas'
print(f'PASS: {len(seen)} hojas CSS locales verificadas')
