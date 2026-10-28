from html.parser import HTMLParser
from pathlib import Path
import runpy
import tempfile

ROOT = Path(__file__).resolve().parents[1]
m = runpy.run_path(str(ROOT / 'scripts/build-atlas-literario.py'))

class CountParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.attrs = []
    def handle_starttag(self, tag, attrs):
        record = dict(attrs)
        if 'data-atlas-count' in record:
            self.attrs.append(record)

with tempfile.TemporaryDirectory() as temporary:
    out = Path(temporary)
    m['build']({'updated': '2026-10-20', 'items': []}, {'bibliotecas': 'Bibliotecas'}, out)
    document = (out / 'index.html').read_text(encoding='utf-8')
    parser = CountParser()
    parser.feed(document)
    assert len(parser.attrs) == 1, 'se espera un contador accesible'
    attrs = parser.attrs[0]
    assert attrs.get('role') == 'status' or attrs.get('aria-live') in {'polite', 'assertive'}, f'contador no anunciado: {attrs}'
print('PASS: contador Atlas accesible')
