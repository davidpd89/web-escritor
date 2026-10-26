from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['index.html', 'accesibilidad/index.html']
TRACKERS = {'gc.zgo.at', 'tracker.metricool.com', 'davidportodiaz.goatcounter.com'}

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'link':
            self.links.append(dict(attrs))

errors = []
for path in PAGES:
    parser = Links()
    parser.feed((ROOT / path).read_text(encoding='utf-8'))
    for link in parser.links:
        relations = set((link.get('rel') or '').lower().split())
        if not relations.intersection({'preconnect', 'dns-prefetch'}):
            continue
        href = link.get('href') or ''
        hostname = (urlsplit(href).hostname or '').lower()
        if hostname in TRACKERS:
            errors.append(f'{path}: conexion especulativa {href} mediante {relations}; debe esperar al consentimiento')
assert not errors, '\n'.join(errors)
print(f'PASS: {len(PAGES)} paginas sin conexiones especulativas a analitica')