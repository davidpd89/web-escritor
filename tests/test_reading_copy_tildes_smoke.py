"""Tildes en lo que cambia la carga: lo mismo que content-index-check, antes de abrir la PR y nombrando el libro.

12/11 (#43155412537): `check-copy-tildes.py` solo corría en la CI de la PR y tumbó el lote por «frances» en
recomendaciones/pagina/10. repair_title_accents ya repara los campos de prosa; este contrato es la red para
cualquier otro campo que acabe en una página. Escanea solo los ficheros cambiados (el repo entero tarda 95 s) y
nombra los libros culpables: la carga los aparta y publica el resto.

El culpable sale del HTML publicado, no de imitar al generador: cada trozo señalado pertenece a la ficha que lo
rodea (`data-book-id` de la tarjeta, enlace a /recomendaciones/libros/<slug>/, o la propia página del libro).
Imitar a mano cómo publica el generador fallaba de tres formas (#1319, Codex y CodeRabbit): la tarjeta recorta la
sinopsis, `sinopsis_breve` se publica con las líneas unidas y los nombres no pasan por `strip_shouting`.
El cotejo por texto queda solo para trozos fuera de toda ficha (JS, cabeceras).
"""
import bisect
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

BOOK_PAGE = re.compile(r'(?:^|/)recomendaciones/libros/([^/]+)/')
BOOK_MARK = re.compile(r'data-book-id="([^"]+)"|href="(?:https?://[^"/]+)?/recomendaciones/libros/([^"/#?]+)/')
# Nombres propios: el generador no les quita las mayúsculas («Frances DE LA TOUR» se publica tal cual).
NAME_FIELDS = {'autores', 'autor', 'editorial', 'sello', 'coleccion', 'traductores', 'ilustradores'}
# Campos que se publican en un solo párrafo aunque el dato traiga saltos de línea.
JOINED_FIELDS = {'sinopsis_breve', 'descripcion_breve'}


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
    """Trozos de un campo para el cotejo por texto (solo fuera de fichas): por párrafos o líneas, el campo entero
    unido, y la versión sin marketing en mayúsculas salvo en los nombres."""
    partes = text.split('\n\n') if key == 'sinopsis_completa' else re.split(r'\n+', text)
    candidatos = [' '.join(p.split()) for p in partes if p.strip()]
    if key in JOINED_FIELDS:
        candidatos.append(' '.join(text.split()))
    out = []
    for parte in dict.fromkeys(candidatos):
        out.append(parte)
        if key not in NAME_FIELDS and strip_shouting(parte) != parte:
            out.append(strip_shouting(parte))
    return out


def published(books):
    return [b for b in books if b.get('estado') != 'borrador']


def culprits(word, books):
    """Cotejo por texto: libros con la palabra sin tilde en algún trozo que no sea técnico.

    Los borradores no se publican: no pueden causar un hallazgo y nombrarlos hacía que `isolate` abortara."""
    pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
    return [b['id'] for b in published(books)
            if any(pattern.search(piece) and not tildes.is_technical_use(piece, word)
                   for key, text in strings(b) for piece in pieces(key, text))]


def mentions(book, word):
    """El libro contiene la palabra en algún dato, en cualquier forma: basta para confirmar una ficha."""
    pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
    return any(pattern.search(text) for _, text in strings(book))


TAG = re.compile(r'<(/?)([A-Za-z][\w-]*)\b[^>]*?(/?)>')
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}


def elements(cleaned):
    """[(inicio, fin, padre)] de cada etiqueta de apertura, en orden; fin = cierre de su elemento (o fin del texto)."""
    out, stack = [], []
    for m in TAG.finditer(cleaned):
        closing, name, selfclose = m.group(1), m.group(2).lower(), m.group(3)
        if closing:
            for k in range(len(stack) - 1, -1, -1):
                if stack[k][0] == name:
                    for _, idx in stack[k:]:
                        out[idx][1] = m.end()
                    del stack[k:]
                    break
            continue
        out.append([m.start(), len(cleaned), stack[-1][1] if stack else None])
        if name in VOID or selfclose:
            out[-1][1] = m.end()
        else:
            stack.append((name, len(out) - 1))
    return out


def marks(cleaned, by_slug):
    """[(inicio, fin, id)]: el ámbito de cada ficha del HTML publicado. Una tarjeta con `data-book-id` cubre su
    elemento; un enlace a la ficha cubre el contenedor del enlace (el `<li>` o la tarjeta). Texto fuera de todo ámbito
    no hereda el libro anterior (CodeRabbit #1319: «Edición en frances» tras dos tarjetas ya cerradas)."""
    tags = elements(cleaned)
    starts = [t[0] for t in tags]
    out = []
    for m in BOOK_MARK.finditer(cleaned):
        book_id = m.group(1) or by_slug.get(m.group(2))
        i = bisect.bisect_right(starts, m.start()) - 1
        if not book_id or i < 0:
            continue
        tag = tags[i]
        if m.group(2) and tag[2] is not None:
            tag = tags[tag[2]]
        out.append((tag[0], tag[1], book_id))
    return out


def owner_at(found, pos):
    """La ficha más interna cuyo ámbito contiene `pos`, o None."""
    inside = [(start, book) for start, end, book in found if start <= pos < end]
    return max(inside)[1] if inside else None


def html_culprits(rel, src, books):
    """[(línea, palabra, texto, ids)] de una página: ids = la ficha que rodea cada trozo señalado."""
    by_id = {b['id']: b for b in published(books)}
    by_slug = {b['slug']: b['id'] for b in by_id.values() if b.get('slug')}
    cleaned, chunks = tildes.html_visible_chunks(src)
    found = marks(cleaned, by_slug)
    page = BOOK_PAGE.search(rel)
    own = by_slug.get(page.group(1)) if page else None
    titles = tildes.own_title_words(rel)
    out = []
    for pos, line, text in chunks:
        for word in tildes.flagged_words(text, text):
            if word in titles:
                continue
            owner = owner_at(found, pos) or own
            if owner in by_id and mentions(by_id[owner], word):
                ids = [owner]
            else:
                # Fuera de toda ficha, o la ficha no tiene la palabra: cotejo por texto entre los libros de la
                # página (o todos, si no enlaza ninguno).
                local = {b for *_, b in found} | ({own} if own else set())
                ids = culprits(word, [by_id[b] for b in local if b in by_id] or books)
            out.append((line, word, re.sub(r'\s+', ' ', text).strip(), ids))
    return out


def report(found):
    """Todos los libros nombrados primero y después el detalle acotado: con muchos hallazgos de un mismo libro, los
    40 primeros podían nombrar solo a ese y la carga apartaba un libro por ronda hasta agotarlas (#1314)."""
    named = (m.group(1) for m in (re.search(r'sin tilde en (.*?) — ', f) for f in found) if m)
    ids = dict.fromkeys(i for group in named if group != 'ningún libro' for i in group.split())
    return '\n'.join(['Libros: ' + ' '.join(ids), *found[:40]] + ([f'… y {len(found) - 40} más'] if len(found) > 40 else []))


def line_of(rel, line, word, text, ids):
    return f'{rel}:{line}: «{word}» sin tilde en {" ".join(ids) or "ningún libro"} — {text[:110]}'


def findings(root, books):
    out = []
    for rel in git_estado.rutas(root):
        path = root / rel
        if not rel.endswith(('.html', '.js')) or not path.is_file():
            continue
        if any(part in tildes.SKIP_PARTS for part in Path(rel).parts):
            continue
        if rel.endswith('.html'):
            src = path.read_text(encoding='utf-8', errors='replace')
            out += [line_of(rel, *hit) for hit in html_culprits(rel, src, books)]
        else:
            out += [line_of(rel, line, word, text, culprits(word, books))
                    for rel, line, word, text in tildes.scan(rel, path)]
    return out


class CopyTildesInChangedFiles(unittest.TestCase):
    def test_changed_pages_keep_their_accents(self):
        books = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))['libros']
        found = findings(ROOT, books)
        self.assertEqual(found, [], report(found))


def card(book_id, text):
    return f'<article data-book-id="{book_id}"><h3>Título</h3><p>{text}</p></article>'


class CulpritFromPublishedPage(unittest.TestCase):
    def test_truncated_card_names_its_book(self):
        """Codex P1: «francés» quedaba después del corte de la tarjeta; por el dato completo parecía técnico."""
        sinopsis = 'Edición en frances revisada. ' + 'x ' * 120 + 'Traducido del francés.'
        books = [{'id': 'isbn-1', 'slug': 'uno-1', 'sinopsis_completa': sinopsis},
                 {'id': 'isbn-2', 'slug': 'dos-2', 'sinopsis_completa': 'Otra novela.'}]
        page = card('isbn-2', 'Otra novela.') + card('isbn-1', 'Edición en frances revisada. x x x…')
        hits = html_culprits('recomendaciones/pagina/2/index.html', page, books)
        self.assertEqual([(w, ids) for _, w, _, ids in hits], [('frances', ['isbn-1'])])

    def test_short_synopsis_published_with_lines_joined(self):
        """CodeRabbit: `sinopsis_breve` se publica en un párrafo; partirla por líneas inventaba o perdía culpables."""
        books = [{'id': 'isbn-3', 'slug': 'tres-3', 'sinopsis_breve': 'Traducción del\nfrances antiguo.'}]
        page = card('isbn-3', 'Traducción del frances antiguo.')
        hits = html_culprits('recomendaciones/index.html', page, books)
        self.assertEqual([ids for *_, ids in hits], [['isbn-3']])
        self.assertEqual(culprits('frances', books), ['isbn-3'])

    def test_author_name_is_not_shouting_stripped(self):
        """CodeRabbit: «Frances DE LA TOUR» se publica tal cual; quitarle mayúsculas lo convertía en culpable."""
        books = [{'id': 'isbn-4', 'slug': 'cuatro-4', 'autores': ['Frances DE LA TOUR']},
                 {'id': 'isbn-5', 'slug': 'cinco-5', 'subtitulo': 'Edición en frances'}]
        self.assertEqual(culprits('frances', books), ['isbn-5'])
        page = card('isbn-4', 'Frances DE LA TOUR') + card('isbn-5', 'Edición en frances')
        hits = html_culprits('recomendaciones/pagina/3/index.html', page, books)
        self.assertEqual([ids for *_, ids in hits], [['isbn-5']])

    def test_link_to_the_book_page_marks_the_card(self):
        books = [{'id': 'isbn-6', 'slug': 'seis-6', 'subtitulo': 'Edición en frances'}]
        page = '<li><a href="/recomendaciones/libros/seis-6/">Seis</a> <span>Edición en frances</span></li>'
        hits = html_culprits('recomendaciones/editoriales/x/index.html', page, books)
        self.assertEqual([ids for *_, ids in hits], [['isbn-6']])

    def test_text_after_closed_cards_does_not_inherit_the_last_one(self):
        """CodeRabbit #1319: un párrafo tras dos tarjetas cerradas no es de la última aunque su autor diga «Frances»."""
        books = [{'id': 'isbn-11', 'slug': 'once-11', 'autores': ['Frances DE LA TOUR']},
                 {'id': 'isbn-12', 'slug': 'doce-12', 'subtitulo': 'Edición en frances'},
                 {'id': 'isbn-13', 'slug': 'trece-13', 'titulo': 'Trece'}]
        page = card('isbn-12', 'Doce') + card('isbn-13', 'Trece') + card('isbn-11', 'Once') + '<p>Edición en frances</p>'
        hits = html_culprits('recomendaciones/pagina/5/index.html', page, books)
        self.assertEqual([ids for *_, ids in hits], [['isbn-12']])

    def test_book_page_owns_text_outside_the_cards(self):
        books = [{'id': 'isbn-14', 'slug': 'catorce-14', 'sinopsis_completa': 'Edición en frances.'},
                 {'id': 'isbn-15', 'slug': 'quince-15', 'autores': ['Frances DE LA TOUR']}]
        page = '<main>' + card('isbn-15', 'Quince') + '<p>Edición en frances.</p></main>'
        hits = html_culprits('recomendaciones/libros/catorce-14/index.html', page, books)
        self.assertEqual([ids for *_, ids in hits], [['isbn-14']])

    def test_book_page_owns_text_before_any_card(self):
        books = [{'id': 'isbn-7', 'slug': 'siete-7', 'sinopsis_completa': 'Edición en frances.'},
                 {'id': 'isbn-8', 'slug': 'ocho-8', 'titulo': 'Ocho'}]
        page = '<main><p>Edición en frances.</p>' + card('isbn-8', 'Ocho') + '</main>'
        hits = html_culprits('recomendaciones/libros/siete-7/index.html', page, books)
        self.assertEqual([ids for *_, ids in hits], [['isbn-7']])

    def test_header_text_falls_back_to_the_books_on_the_page(self):
        books = [{'id': 'isbn-9', 'slug': 'nueve-9', 'subtitulo': 'Edición en frances'},
                 {'id': 'isbn-10', 'slug': 'diez-10', 'subtitulo': 'Edición en frances'}]
        page = '<h1>Edición en frances</h1>' + card('isbn-9', 'Nueve')
        hits = html_culprits('recomendaciones/pagina/4/index.html', page, books)
        self.assertEqual([ids for *_, ids in hits], [['isbn-9']])

    def test_line_numbers_match_the_checker(self):
        page = '<p>uno</p>\n<!-- a\nb -->\n<script>\nx\n</script>\n<p>Edición en frances</p>'
        self.assertEqual([line for line, *_ in html_culprits('a/index.html', page, [])],
                         [line for line, text, _ in tildes.html_visible_text(page) if 'frances' in text])
        self.assertEqual([line for line, *_ in html_culprits('a/index.html', page, [])], [7])


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
