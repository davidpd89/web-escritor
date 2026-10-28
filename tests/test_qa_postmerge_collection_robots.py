import importlib.util
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sitemap_robots', ROOT / 'scripts/build-sitemap.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class Robots(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and a.get('name', '').lower() in ('robots', 'googlebot'):
            self.values.append(a.get('content', ''))

urls = module.collect_urls(ROOT)
for rel in ('cuaderno/index.html', 'editoriales/index.html', 'recomendaciones/index.html'):
    path = ROOT / rel
    html = path.read_text(encoding='utf-8')
    parser = Robots()
    parser.feed(html)
    canonical, noindex, _ = module.extract_meta(html)
    assert not noindex, f'{rel}: extract_meta detecta noindex'
    for value in parser.values:
        directives = {part.strip().lower() for part in value.split(',')}
        assert 'noindex' not in directives, f'{rel}: robots contiene noindex: {value!r}'
        assert 'nofollow' not in directives, f'{rel}: robots contiene nofollow: {value!r}'
    loc = module.normalize_canonical(canonical, ROOT, path)
    assert loc in urls, f'{rel}: página indexable ausente del sitemap: {loc}'

robots = (ROOT / 'robots.txt').read_text(encoding='utf-8')
lines = [line.strip() for line in robots.splitlines() if line.strip() and not line.lstrip().startswith('#')]
assert 'Sitemap: https://davidportodiaz.com/sitemap.xml' in lines, 'robots.txt: sitemap público ausente o incorrecto'
print('OK: indexación y descubrimiento de colecciones')