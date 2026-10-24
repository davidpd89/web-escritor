import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
published = [b for b in data['libros'] if b['estado'] == 'publicado' and b.get('editorial_catalogo_slug')]
assert published, 'No hay sellos activos que recorrer'
for b in published:
    base = '/recomendaciones/editoriales/' + b['editorial_catalogo_slug'] + '/'
    book = '/recomendaciones/libros/' + b['slug'] + '/'
    detail = (ROOT / book.lstrip('/') / 'index.html').read_text(encoding='utf-8')
    directory = (ROOT / base.lstrip('/') / 'index.html').read_text(encoding='utf-8')
    assert 'href="' + base + '"' in detail, (b['id'], 'sin enlace de ida')
    assert 'href="' + book + '"' in directory, (b['id'], 'sin enlace de retorno')
print('reading publisher reverse links: OK')
