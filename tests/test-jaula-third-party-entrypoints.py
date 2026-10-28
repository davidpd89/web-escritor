from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PAGE = 'donde-empieza-la-jaula/index.html'
TRACKERS = ('goatcounter.com', 'gc.zgo.at', 'metricool.com', 'clarity.ms', 'bing.com')

class Resources(HTMLParser):
    def __init__(self):
        super().__init__()
        self.resources = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'script' and a.get('src'):
            self.resources.append((tag, a['src']))
        if tag == 'iframe' and a.get('src'):
            self.resources.append((tag, a['src']))
        if tag == 'img' and a.get('src'):
            self.resources.append((tag, a['src']))
        if tag == 'link' and (a.get('rel') or '').lower() in ('preload', 'preconnect', 'dns-prefetch'):
            self.resources.append((tag, a.get('href', '')))

parser = Resources()
parser.feed((ROOT / PAGE).read_text(encoding='utf-8'))
for tag, url in parser.resources:
    parsed = urlparse('https:' + url if url.startswith('//') else url)
    host = (parsed.hostname or '').lower()
    for tracker in TRACKERS:
        assert host != tracker and not host.endswith('.' + tracker), f'{PAGE}: {tag} activa tercero {url} sin mediación del consentimiento'
print(f'OK: {PAGE}: {len(parser.resources)} recursos inspeccionados sin rastreadores directos')