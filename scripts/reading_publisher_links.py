"""Publisher back-links derived exclusively from the public reading catalogue."""
import html
import json
from pathlib import Path


def render_books(publisher_slug, root=None):
    root = Path(root) if root else Path(__file__).resolve().parents[1]
    path = root / 'data/reading-catalogue.json'
    if not path.exists():
        return ''
    books = [b for b in json.loads(path.read_text(encoding='utf-8'))['libros']
             if b['estado'] == 'publicado' and b.get('editorial_slug') == publisher_slug]
    if not books:
        return ''
    esc = html.escape
    links = ''.join('<li><a href="/recomendaciones/libros/' + esc(b['slug'], quote=True) + '/">' + esc(b['titulo']) + '</a> — ' + esc(', '.join(b['autores'])) + '</li>' for b in books)
    return '<div class="tool-findings-block"><h2>Libros de este sello en el catálogo de lectura</h2><ul class="tool-findings">' + links + '</ul><p><a class="text-action" href="/recomendaciones/">Explorar todos los libros</a></p></div>'
