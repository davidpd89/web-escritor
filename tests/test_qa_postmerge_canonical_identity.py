import importlib.util
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sitemap_under_test', ROOT / 'scripts/build-sitemap.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonicals = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'link' and 'canonical' in a.get('rel', '').lower().split():
            self.canonicals.append(a.get('href', ''))

pages = {
    'index.html': 'https://davidportodiaz.com/',
    'cuaderno/index.html': 'https://davidportodiaz.com/cuaderno/',
    'editoriales/index.html': 'https://davidportodiaz.com/editoriales/',
    'recomendaciones/index.html': 'https://davidportodiaz.com/recomendaciones/',
}
urls = module.collect_urls(ROOT)
for rel, expected in pages.items():
    path = ROOT / rel
    parser = Links()
    parser.feed(path.read_text(encoding='utf-8'))
    assert parser.canonicals == [expected], f'{rel}: canonical={parser.canonicals!r}, esperado={expected}'
    assert module.normalize_canonical(expected, ROOT, path) == expected, f'{rel}: normalización altera {expected}'
    assert expected in urls, f'{rel}: falta {expected} en collect_urls'
print('OK: identidad canonical y sitemap de cuatro páginas principales')