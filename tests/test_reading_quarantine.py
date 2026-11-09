"""Cuarentena por libro: un dato malo aparta su libro y el resto del lote sigue validando."""
import copy
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reading_quarantine as q  # noqa: E402

DATA = json.loads((ROOT / q.CATALOGUE).read_text(encoding='utf-8'))


def without(n):
    """Catálogo sin el libro n y ese libro con sus categorías: así el libro llega como nuevo en la carga."""
    data = copy.deepcopy(DATA)
    book = data['libros'].pop(n)
    cats = sorted(r['categoria_id'] for r in data['libro_categorias'] if r['libro_id'] == book['id'])
    data['libro_categorias'] = [r for r in data['libro_categorias'] if r['libro_id'] != book['id']]
    return data, book, cats


class QuarantineTest(unittest.TestCase):
    def test_bad_new_book_leaves_the_batch(self):
        before, book, cats = without(0)
        data = copy.deepcopy(DATA)
        data['libros'][0]['autores'] = []
        clean, out = q.isolate(data, ROOT, before, today='2026-11-03')
        self.assertEqual([h['libro']['id'] for h in out], [book['id']])
        self.assertTrue(out[0]['motivo'].startswith(book['id']))
        self.assertEqual(out[0]['categorias'], cats)
        self.assertEqual(clean, before)

    def test_bad_update_keeps_the_published_version(self):
        data = copy.deepcopy(DATA)
        data['libros'][3]['descripcion_breve'] = 'corta'
        clean, out = q.isolate(data, ROOT, DATA)
        self.assertEqual(out[0]['libro']['descripcion_breve'], 'corta')
        self.assertEqual(clean, DATA)

    def test_good_books_are_untouched_and_retried(self):
        data, book, cats = without(1)
        held = [{'libro': book, 'categorias': cats, 'motivo': 'x', 'desde': '2026-10-01'}]
        clean, out = q.isolate(data, ROOT, data, held)
        self.assertEqual(out, [])
        self.assertIn(book, clean['libros'])
        self.assertEqual(q.isolate(DATA, ROOT, DATA), (DATA, []))

    def test_still_bad_held_book_keeps_its_date(self):
        data, book, cats = without(2)
        book['autores'] = []
        held = [{'libro': book, 'categorias': cats, 'motivo': 'x', 'desde': '2026-10-01'}]
        clean, out = q.isolate(data, ROOT, data, held, today='2026-11-03')
        self.assertEqual(clean, data)
        self.assertEqual(out[0]['desde'], '2026-10-01')

    def test_rule_errors_still_stop_the_batch(self):
        data = copy.deepcopy(DATA)
        data['categorias'][0]['tipo'] = 'inventado'
        with self.assertRaises(q.build.ValidationError):
            q.isolate(data, ROOT, DATA)
        broken = copy.deepcopy(DATA)
        broken['libros'][0]['descripcion_breve'] = 'corta'
        with self.assertRaises(q.build.ValidationError):  # publicado y sin cambios: no se despublica en silencio
            q.isolate(broken, ROOT, broken)

    def test_too_many_books_is_a_rule_problem(self):
        data = copy.deepcopy(DATA)
        for b in data['libros'][:q.MAX_BOOKS + 1]:
            b['descripcion_breve'] = 'corta'
        with self.assertRaises(q.build.ValidationError):
            q.isolate(data, ROOT, DATA)

    def test_duplicate_cover_blames_the_changed_book(self):
        # Ingesta 42588397174: el tomo que cambió tomó la portada de otro ya publicado; se apartaba al publicado
        # (sin cambios) y la carga entera fallaba.
        data = copy.deepcopy(DATA)
        for key in ('portada_local', 'portada_ancho', 'portada_alto'):
            data['libros'][0][key] = data['libros'][5][key]
        clean, out = q.isolate(data, ROOT, DATA)
        self.assertEqual([h['libro']['id'] for h in out], [DATA['libros'][0]['id']])
        self.assertIn('igual que', out[0]['motivo'])
        self.assertEqual(clean, DATA)

    def test_restore_cover_brings_back_the_published_file(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cover = root / 'assets/reading-covers/isbn-1.webp'
            cover.parent.mkdir(parents=True)
            cover.write_bytes(b'publicada')
            for cmd in (['init', '-q'], ['add', '.'], ['-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'x']):
                subprocess.run(['git', *cmd], cwd=root, check=True)
            cover.write_bytes(b'nueva de amazon')
            q.restore_cover(root, {'portada_local': '/assets/reading-covers/isbn-1.webp'})
            self.assertEqual(cover.read_bytes(), b'publicada')

    def test_culprit_is_a_known_book_id(self):
        first = DATA['libros'][0]['id']
        self.assertEqual(q.culprit(f'{first}: falta edicion', DATA), first)
        self.assertEqual(q.culprit(f'{first}.mes: fecha inválida', DATA), first)
        self.assertIsNone(q.culprit('Relación duplicada o referencia inexistente', DATA))


    def test_100_books_20_bad_the_80_good_continue(self):
        """Llegan 100 libros, 20 traen datos rotos: los 80 válidos siguen y los 20 quedan trazados."""
        incoming = DATA['libros'][:100]
        ids = {b['id'] for b in incoming}
        before = copy.deepcopy(DATA)
        before['libros'] = [b for b in before['libros'] if b['id'] not in ids]
        before['libro_categorias'] = [r for r in before['libro_categorias'] if r['libro_id'] not in ids]
        data = copy.deepcopy(DATA)
        bad = {b['id'] for b in data['libros'][:100:5]}
        for b in data['libros'][:100:5]:
            b['autores'] = []
        clean, out = q.isolate(data, ROOT, before, today='2026-11-04')
        self.assertEqual({h['libro']['id'] for h in out}, bad)
        self.assertEqual(len(out), 20)
        published = {b['id'] for b in clean['libros']}
        self.assertEqual(len(ids & published), 80)
        self.assertFalse(bad & published)
        for h in out:
            self.assertEqual(h['isbn'], h['libro'].get('isbn13', ''))
            self.assertEqual(h['intentos'], 1)
            self.assertTrue(h['causa'] and h['libro']['id'] not in h['causa'])
        self.assertEqual(len({h['causa'] for h in out}), 1, 'los 20 comparten causa y se agrupan')

    def test_more_than_half_the_batch_is_global(self):
        incoming = DATA['libros'][:30]
        ids = {b['id'] for b in incoming}
        before = copy.deepcopy(DATA)
        before['libros'] = [b for b in before['libros'] if b['id'] not in ids]
        before['libro_categorias'] = [r for r in before['libro_categorias'] if r['libro_id'] not in ids]
        data = copy.deepcopy(DATA)
        for b in data['libros'][:16]:
            b['autores'] = []
        with self.assertRaisesRegex(q.build.ValidationError, 'Error global'):
            q.isolate(data, ROOT, before)

    def test_attempts_accumulate_and_pending_recover_after_fix(self):
        data, book, cats = without(4)
        broken = copy.deepcopy(book)
        broken['autores'] = []
        held = [{'libro': broken, 'categorias': cats, 'motivo': 'x', 'desde': '2026-10-01', 'intentos': 2}]
        _, out = q.isolate(data, ROOT, data, held, today='2026-11-04')
        self.assertEqual((out[0]['intentos'], out[0]['desde']), (3, '2026-10-01'))
        # La regla (o el dato de origen) se corrige: el pendiente vuelve al catálogo sin tocarlo a mano.
        held[0]['libro'] = book
        clean, out = q.isolate(data, ROOT, data, held)
        self.assertEqual(out, [])
        self.assertIn(book, clean['libros'])

    def test_cause_is_groupable(self):
        self.assertEqual(q.cause('isbn-9788410427709: sello del catálogo inexistente'), 'sello del catálogo inexistente')
        self.assertEqual(q.cause('lib-0042.mes: fecha inválida 13'), 'mes: fecha inválida N')
        self.assertEqual(q.cause('AttributeError: x'), 'AttributeError: x')

    def test_missing_catalogue_publisher_is_repaired_for_every_book(self):
        """Regresión #1152: el sello perdido se registra desde la ficha oficial y el libro deja de estar apartado."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'data').mkdir()
            for name in ('reading-publishers.json', 'editoriales.json', 'reading-intake-config.json'):
                shutil.copy(ROOT / 'data' / name, root / 'data' / name)
            store = json.loads((root / q.PUBLISHERS).read_text(encoding='utf-8'))
            store['editoriales'] = [p for p in store['editoriales'] if p['slug'] != 'neko-books']
            (root / q.PUBLISHERS).write_text(json.dumps(store, ensure_ascii=False), encoding='utf-8')
            books = [{'id': f'isbn-97884104277{i:02d}', 'editorial': 'Neko Books', 'editorial_catalogo_slug': 'neko-books',
                      'fuente_publicacion_url': f'https://www.planetadelibros.com/libro-x/{i}'} for i in range(3)]
            self.assertEqual(q.repair_catalogue_publishers(books, root, '2026-11-04'), 3)
            slugs = {p['slug'] for p in json.loads((root / q.PUBLISHERS).read_text(encoding='utf-8'))['editoriales']}
            self.assertIn('neko-books', slugs)
            self.assertEqual(q.repair_catalogue_publishers(books, root, '2026-11-04'), 0, 'idempotente')

    def test_carry_moves_every_file_the_intake_writes(self):
        """Regresión #1152: todo lo que la ingesta escribe en data/ viaja con el carry de una PR obsoleta."""
        intake = (ROOT / 'scripts/reading_intake_pipeline.py').read_text(encoding='utf-8')
        refresh = (ROOT / 'scripts/refresh-reading-catalogue.py').read_text(encoding='utf-8')
        written = set(re.findall(r"write_if_changed\(root / '(data/[^']+)'", intake))
        carried = set(re.findall(r"'([^']+)'", re.search(r'SOURCE_PATHS = \(([^)]*)\)', refresh)[1]))
        self.assertTrue(written)
        self.assertLessEqual(written, carried)


    def test_book_with_only_inactive_categories_is_named(self):
        data = copy.deepcopy(DATA)
        book = next(b for b in data['libros'] if b['estado'] == 'publicado')
        own = {r['categoria_id'] for r in data['libro_categorias'] if r['libro_id'] == book['id']}
        for c in data['categorias']:
            if c['id'] in own:
                c['activa'] = False
        with self.assertRaisesRegex(q.build.ValidationError, re.escape(book['id'] + ': sin categoría activa')):
            q.build.validate(data, ROOT)

    def test_source_text_without_accents_is_repaired_for_every_book(self):
        # sync 42444782344 / #1228: 38 avisos de check-copy-tildes en content-index-check por tres títulos.
        books = [{'titulo': 'Matteo. Edicion integral: 1', 'descripcion_breve': 'Matteo. Edicion integral: 1, de Gibrat.'},
                 {'titulo': 'La balada del norte 03 (nueva edicion)', 'sinopsis_breve': 'Novela historica y EDICION nueva.'},
                 {'titulo': "En mi Era Pistacho: Juliette's version"},
                 {'titulo': 'Las versiones de Frances Burney', 'fuente_publicacion_url': 'https://x.es/edicion-especial'}]
        self.assertEqual(q.repair_title_accents(books, ROOT, '2026-11-08'), 4)  # campos reparados
        self.assertEqual(books[0]['titulo'], 'Matteo. Edición integral: 1')
        self.assertEqual(books[0]['descripcion_breve'], 'Matteo. Edición integral: 1, de Gibrat.')
        self.assertEqual(books[1]['titulo'], 'La balada del norte 03 (nueva edición)')
        self.assertEqual(books[1]['sinopsis_breve'], 'Novela histórica y EDICIÓN nueva.')
        self.assertEqual(books[2]['titulo'], "En mi Era Pistacho: Juliette's version")  # inglés tras posesivo
        self.assertEqual(books[3]['titulo'], 'Las versiones de Frances Burney')  # plural y nombre propio
        self.assertEqual(q.repair_title_accents(books, ROOT, '2026-11-08'), 0)  # idempotente

    def test_checker_reads_entities_as_the_reader_does(self):
        page = '<p>En mi Era Pistacho: Juliette&#x27;s version</p><p>Nueva edicion</p>'
        pieces = [text for _, text, _ in q.tildes.html_visible_text(page)]
        self.assertEqual(pieces[0], "En mi Era Pistacho: Juliette's version")
        flagged = [w for t in pieces for w in q.tildes.WORD_RE.findall(t) if not q.tildes.is_technical_use(t, w.lower())]
        self.assertEqual(flagged, ['edicion'])


if __name__ == '__main__':
    unittest.main()
