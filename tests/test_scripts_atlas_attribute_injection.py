from html.parser import HTMLParser
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
m = runpy.run_path(str(ROOT / 'scripts/build-atlas-literario.py'))

class ArticleAttributes(HTMLParser):
    def __init__(self):
        super().__init__()
        self.attrs = None
    def handle_starttag(self, tag, attrs):
        if tag == 'article' and self.attrs is None:
            self.attrs = dict(attrs)

for category in ['bibliotecas', 'bibliotecas" onmouseover="alert(1)', 'rutas" onclick="alert(2)']:
    item = {
        'slug': 'ficha-prueba',
        'title': 'Ruta de prueba',
        'summary': 'Una descripción documental.',
        'country': 'España',
        'category': category
    }
    result = m['card'](item, {category: 'Rutas documentadas'})
    parser = ArticleAttributes()
    parser.feed(result)
    assert parser.attrs is not None
    assert parser.attrs['data-category'] == category, 'el valor se ha truncado o alterado'
    assert not any(key.startswith('on') for key in parser.attrs), f'atributo ejecutable inyectado: {parser.attrs}'
print('PASS: atributos de categorías aislados')
