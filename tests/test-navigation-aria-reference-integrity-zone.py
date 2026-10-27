from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['index.html', 'mapa-del-sitio/index.html', 'empieza-aqui/index.html']

class AriaAudit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.references = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            self.ids.append(a['id'])
        if tag in ('button', 'a', 'nav'):
            for key in ('aria-controls', 'aria-labelledby'):
                if a.get(key):
                    for ref in a[key].split():
                        self.references.append((tag, key, ref))

for page in PAGES:
    parser = AriaAudit()
    parser.feed((ROOT / page).read_text(encoding='utf-8'))
    counts = Counter(parser.ids)
    errors = [f'{tag}[{key}] -> {ref} ({counts[ref]} coincidencias)' for tag, key, ref in parser.references if counts[ref] != 1]
    assert not errors, f'{page}: ' + '; '.join(errors)
print('navigation-aria-reference-integrity: OK')
