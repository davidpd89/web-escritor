"""Buscar por ISBN en /recomendaciones/ da exactamente su libro, para todos los libros publicados.

Antes lo comprobaba qa/reading-intake-browser.mjs tecleando cada ISBN en el navegador: con 4945 libros eran 4945
búsquedas sobre 5028 tarjetas (cuadrático, >10 min en local) y con 1000 más no cabía en los 25 min del job (15/11).
Aquí se comprueba lo mismo en lineal sobre el HTML publicado; el navegador ya solo repite una muestra.

El buscador (assets/reading-catalogue.js) compara por subcadena el texto normalizado de título, autor e ISBN de cada
tarjeta: un ISBN encuentra exactamente su libro si está en su tarjeta, no se repite en otra y ningún título o autor
contiene esos 13 dígitos.

Es contrato de datos (tests/test_*_smoke.py, lo corre check-reading-data antes de abrir la PR): cada fallo nombra los
libros afectados para que la carga los aparte en vez de perder el lote.
"""
import html
import json
import re
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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
    publicados = {b['id'] for b in libros}
    sobran = [t.get('book-id') for t in tarjetas if t.get('book-id') not in publicados]
    if sobran:
        fallos.append(f"tarjetas de libros no publicados: {', '.join(map(str, sobran))}")
    con_isbn = {}
    for t in tarjetas:
        if t.get('isbn'):
            con_isbn.setdefault(t['isbn'], []).append(t.get('book-id'))
    isbns = Counter({i: len(ids) for i, ids in con_isbn.items()})
    # Los mensajes nombran solo el id culpable: la carga aparta todo id que aparezca en un fallo de contrato
    # (reading_quarantine.flagged_books), así que el libro afectado se cita por su ISBN, nunca por su id.
    # Un ISBN repetido no tiene culpable aquí (el builder ya veta isbn13 duplicados): lo nombra la comprobación por libro.
    fallos += [f"ISBN {i} en {len(ids)} tarjetas: su búsqueda no da un solo libro"
               for i, ids in con_isbn.items() if len(ids) > 1]
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
                    fallos.append(f"{t.get('book-id')}: su título o autor contiene el ISBN {run[k:k + 13]} de otra ficha")
    return fallos


def publicadas(root):
    # La primera página trae unas tarjetas; el JS hidrata el resto desde /recomendaciones/pagina/N/.
    paginas = [root / 'recomendaciones/index.html', *sorted((root / 'recomendaciones/pagina').glob('*/index.html'))]
    return ''.join(f.read_text(encoding='utf-8') for f in paginas)


class BusquedaPorIsbn(unittest.TestCase):
    def test_el_detector_ve_cada_clase_de_fallo(self):
        falso = {'libros': [{'id': 'libro-a', 'estado': 'publicado', 'isbn13': '9780000000001'},
                            {'id': 'libro-b', 'estado': 'publicado', 'isbn13': '9780000000002'},
                            {'id': 'libro-c', 'estado': 'publicado', 'isbn13': '9780000000003'}]}
        pagina = ('<article data-catalogue-book data-book-id="libro-a" data-title="T" data-isbn="9780000000001">'
                  '<article data-catalogue-book data-book-id="libro-b" data-title="T" data-isbn="9780000000001">'
                  '<article data-catalogue-book data-book-id="libro-c" data-title="T 9780000000001" data-isbn="9780000000003">'
                  '<article data-catalogue-book data-book-id="libro-d" data-title="T" data-isbn="9780000000004">')
        detectados = '\n'.join(problemas(falso, pagina))
        self.assertIn('ISBN 9780000000001 en 2 tarjetas', detectados)
        self.assertIn('libro-b: la tarjeta lleva', detectados)
        self.assertIn('libro-c: su título o autor contiene el ISBN 9780000000001 de otra ficha', detectados)
        # Solo los culpables (libro-b, libro-c, libro-d) aparecen por id; libro-a no ha hecho nada.
        self.assertNotIn('libro-a', detectados)
        self.assertIn('no publicados: libro-d', detectados)

    def test_cada_libro_publicado_se_encuentra_por_su_isbn(self):
        catalogue = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        fallos = problemas(catalogue, publicadas(ROOT))
        self.assertFalse(fallos, '\n'.join(fallos[:200]))


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT
    catalogue = json.loads((root / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
    page = publicadas(root)
    fallos = problemas(catalogue, page)
    if fallos:
        print('\n'.join(fallos[:40]))
        print(f'FAIL: {len(fallos)} problemas de búsqueda por ISBN')
        return 1
    print(f'PASS: los {len(list(cards(page)))} libros se encuentran por su ISBN y solo ellos')
    return 0


if __name__ == '__main__':
    sys.exit(main())
