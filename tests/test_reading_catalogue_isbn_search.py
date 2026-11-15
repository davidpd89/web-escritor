"""Buscar por ISBN en /recomendaciones/ da exactamente su libro, para todos los libros publicados.

Antes lo comprobaba qa/reading-intake-browser.mjs tecleando cada ISBN en el navegador: con 4945 libros eran 4945
búsquedas sobre 5028 tarjetas (cuadrático, >10 min en local) y con 1000 más no cabía en los 25 min del job (15/11).
Aquí se comprueba lo mismo en lineal sobre el HTML publicado; el navegador ya solo repite una muestra.

El buscador (assets/reading-catalogue.js) compara por subcadena el texto normalizado de título, autor e ISBN de cada
tarjeta: un ISBN encuentra exactamente su libro si está en su tarjeta, no se repite en otra y ningún título o autor
contiene esos 13 dígitos.
"""
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
CARD = re.compile(r'<[a-z]+\s[^>]*\bdata-catalogue-book\b[^>]*>')
ATTR = re.compile(r'\bdata-([a-z-]+)="([^"]*)"')


def cards(page):
    for tag in CARD.findall(page):
        yield {k: html.unescape(v) for k, v in ATTR.findall(tag)}


def problemas(catalogue, page):
    libros = [b for b in catalogue['libros'] if b.get('estado') == 'publicado']
    tarjetas = list(cards(page))
    por_id = {t.get('book-id'): t for t in tarjetas}
    fallos = []
    if len(tarjetas) != len(libros):
        fallos.append(f'{len(tarjetas)} tarjetas para {len(libros)} libros publicados')
    isbns = Counter(t.get('isbn') for t in tarjetas if t.get('isbn'))
    fallos += [f'ISBN {i} en {n} tarjetas: su búsqueda no da un solo libro' for i, n in isbns.items() if n > 1]
    for b in libros:
        t = por_id.get(b['id'])
        if t is None:
            fallos.append(f"{b['id']}: sin tarjeta en /recomendaciones/")
        elif b.get('isbn13') and t.get('isbn') != b['isbn13']:
            fallos.append(f"{b['id']}: la tarjeta lleva ISBN {t.get('isbn')!r} y el libro {b['isbn13']}")
    for t in tarjetas:
        for run in re.findall(r'\d{13,}', f"{t.get('title', '')} {t.get('author', '')}"):
            for k in range(len(run) - 12):
                if run[k:k + 13] in isbns and run[k:k + 13] != t.get('isbn'):
                    fallos.append(f"{t.get('book-id')}: su título o autor contiene el ISBN {run[k:k + 13]} de otro libro")
    return fallos


def main():
    catalogue = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
    # La primera página trae unas tarjetas; el JS hidrata el resto desde /recomendaciones/pagina/N/.
    paginas = [ROOT / 'recomendaciones/index.html', *sorted((ROOT / 'recomendaciones/pagina').glob('*/index.html'))]
    page = ''.join(f.read_text(encoding='utf-8') for f in paginas)
    fallos = problemas(catalogue, page)

    # Autocomprobación: el detector ve un ISBN repetido, uno cambiado y uno que asoma en el título de otro.
    falso = {'libros': [{'id': 'a', 'estado': 'publicado', 'isbn13': '9780000000001'},
                        {'id': 'b', 'estado': 'publicado', 'isbn13': '9780000000002'},
                        {'id': 'c', 'estado': 'publicado', 'isbn13': '9780000000003'}]}
    pagina = ('<article data-catalogue-book data-book-id="a" data-title="T" data-isbn="9780000000001">'
              '<article data-catalogue-book data-book-id="b" data-title="T" data-isbn="9780000000001">'
              '<article data-catalogue-book data-book-id="c" data-title="T 9780000000001" data-isbn="9780000000003">')
    detectados = problemas(falso, pagina)
    assert any('en 2 tarjetas' in f for f in detectados), detectados
    assert any('b: la tarjeta lleva' in f for f in detectados), detectados
    assert any('contiene el ISBN' in f for f in detectados), detectados

    if fallos:
        print('\n'.join(fallos[:40]))
        print(f'FAIL: {len(fallos)} problemas de búsqueda por ISBN')
        return 1
    print(f'PASS: los {len(list(cards(page)))} libros se encuentran por su ISBN y solo ellos')
    return 0


if __name__ == '__main__':
    sys.exit(main())
