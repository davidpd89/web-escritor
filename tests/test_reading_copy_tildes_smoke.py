"""Tildes en lo que cambia la carga: lo mismo que content-index-check, antes de abrir la PR y nombrando el libro.

12/11 (#43155412537): `check-copy-tildes.py` solo corría en la CI de la PR y tumbó el lote por «frances» en
recomendaciones/pagina/10. repair_title_accents ya repara los campos de prosa; este contrato es la red para
cualquier otro campo que acabe en una página. Escanea solo los ficheros cambiados (el repo entero tarda 95 s) y
nombra los libros cuyo texto contiene la palabra señalada: la carga los aparta y publica el resto.
"""
import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import git_estado  # noqa: E402
from reading_intake_core import strip_shouting  # noqa: E402

spec = importlib.util.spec_from_file_location('check_copy_tildes_contract', ROOT / 'scripts/check-copy-tildes.py')
tildes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tildes)


def strings(value, key=None):
    """(campo, texto) de cada cadena del libro, con el nombre del campo que la contiene."""
    if isinstance(value, str):
        yield key, value
    elif isinstance(value, dict):
        for k, item in value.items():
            yield from strings(item, k)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item, key)


def pieces(key, text):
    """Los trozos tal como se publican, que es lo que `scan` lee.

    La sinopsis se parte solo por párrafos (dos saltos), como `synopsis_paragraphs` del generador; el resto, por
    líneas. A cada trozo se le quita además el marketing en mayúsculas como hace el generador: «EN FRANCES
    ORIGINAL» pasa por técnico en el dato y se publica «en frances original» (#1314, CodeRabbit)."""
    partes = text.split('\n\n') if key == 'sinopsis_completa' else re.split(r'\n+', text)
    out = []
    for parte in (' '.join(p.split()) for p in partes if p.strip()):
        out.append(parte)
        limpia = strip_shouting(parte)
        if limpia != parte:
            out.append(limpia)
    return out


def culprits(word, books):
    """Libros con la palabra sin tilde en algún texto que no sea técnico (ruta, slug, nombre propio).

    Se decide por trozo publicado, como `scan`: con «en frances» en un párrafo y «en francés» en otro, mirar el campo
    entero lo daba por técnico, el libro quedaba sin nombrar y la carga abortaba el lote (#1314, CodeRabbit).
    Los borradores no se publican: no pueden causar un hallazgo y nombrarlos hacía que `isolate` abortara.
    """
    pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
    return [b['id'] for b in books if b.get('estado') != 'borrador'
            if any(pattern.search(piece) and not tildes.is_technical_use(piece, word)
                   for key, text in strings(b) for piece in pieces(key, text))]


def report(found):
    """Todos los libros nombrados primero y después el detalle acotado: con muchos hallazgos de un mismo libro, los
    40 primeros podían nombrar solo a ese y la carga apartaba un libro por ronda hasta agotarlas (#1314)."""
    named = (m.group(1) for m in (re.search(r'sin tilde en (.*?) — ', f) for f in found) if m)
    ids = dict.fromkeys(i for group in named if group != 'ningún libro' for i in group.split())
    return '\n'.join(['Libros: ' + ' '.join(ids), *found[:40]] + ([f'… y {len(found) - 40} más'] if len(found) > 40 else []))


def findings(root, books):
    out = []
    for rel in git_estado.rutas(root):
        path = root / rel
        if not rel.endswith(('.html', '.js')) or not path.is_file():
            continue
        if any(part in tildes.SKIP_PARTS for part in Path(rel).parts):
            continue
        for rel, line, word, text in tildes.scan(rel, path):
            out.append(f'{rel}:{line}: «{word}» sin tilde en {" ".join(culprits(word, books)) or "ningún libro"} — {text[:110]}')
    return out


class CopyTildesInChangedFiles(unittest.TestCase):
    def test_changed_pages_keep_their_accents(self):
        books = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))['libros']
        found = findings(ROOT, books)
        self.assertEqual(found, [], report(found))


class CulpritRule(unittest.TestCase):
    def test_names_the_book_whose_text_lacks_the_accent(self):
        books = [{'id': 'isbn-1', 'titulo': 'Un clásico', 'subtitulo': 'Edición en frances'},
                 {'id': 'isbn-2', 'titulo': 'Cartas', 'autores': ['Frances Burney']},
                 {'id': 'isbn-3', 'titulo': 'Otro', 'url': 'https://x.es/frances-libro'}]
        self.assertEqual(culprits('frances', books), ['isbn-1'])

    def test_shouting_removed_by_the_generator_is_seen(self):
        books = [{'id': 'isbn-7', 'sinopsis_completa': 'Esta novela cuenta una aventura EN FRANCES ORIGINAL que '
                                                        'transforma la vida de todos sus protagonistas.'}]
        self.assertEqual(culprits('frances', books), ['isbn-7'])

    def test_a_draft_does_not_take_the_blame(self):
        books = [{'id': 'isbn-5', 'estado': 'publicado', 'subtitulo': 'Edición en frances'},
                 {'id': 'isbn-6', 'estado': 'borrador', 'subtitulo': 'Edición en frances'}]
        self.assertEqual(culprits('frances', books), ['isbn-5'])

    def test_synopsis_single_line_break_stays_in_one_paragraph(self):
        books = [{'id': 'isbn-8', 'sinopsis_completa': 'Traducido del francés.\nEdición en frances revisada.'},
                 {'id': 'isbn-9', 'subtitulo': 'Edición en frances'}]
        self.assertEqual(culprits('frances', books), ['isbn-9'])

    def test_a_correct_paragraph_does_not_hide_a_wrong_one(self):
        books = [{'id': 'isbn-4', 'sinopsis_completa': 'Traducido del francés.\n\nEdición en frances revisada.'}]
        self.assertEqual(culprits('frances', books), ['isbn-4'])

    def test_report_names_every_book_even_past_the_detail_limit(self):
        found = [f'p.html:{n}: «frances» sin tilde en isbn-{n // 40} — texto' for n in range(160)]
        first = report(found).splitlines()[0]
        self.assertEqual(first, 'Libros: isbn-0 isbn-1 isbn-2 isbn-3')


if __name__ == '__main__':
    unittest.main()
