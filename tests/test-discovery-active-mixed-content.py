from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['recomendaciones', 'cuaderno', 'herramientas', 'editoriales', 'libros']

class Resources(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'script' and a.get('src'):
            self.urls.append(('script', a['src']))
        if tag == 'link':
            rel = set(a.get('rel', '').lower().split())
            if rel.intersection({'stylesheet', 'modulepreload', 'preconnect', 'dns-prefetch'}) or ('preload' in rel and a.get('as') in {'script', 'style'}):
                if a.get('href'):
                    self.urls.append(('link', a['href']))

for name in PAGES:
    parser = Resources()
    parser.feed((ROOT / name / 'index.html').read_text(encoding='utf-8'))
    assert parser.urls, f'/{name}/: no se encontraron recursos activos'
    for kind, url in parser.urls:
        parsed = urlsplit(url)
        assert parsed.scheme.lower() != 'http', f'/{name}/: {kind} utiliza HTTP: {url}'
        assert not url.startswith('//'), f'/{name}/: {kind} utiliza URL dependiente del protocolo: {url}'
    print(f'PASS /{name}/ active resources')
