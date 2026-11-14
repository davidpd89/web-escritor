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

spec = importlib.util.spec_from_file_location('check_copy_tildes_contract', ROOT / 'scripts/check-copy-tildes.py')
tildes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tildes)


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def culprits(word, books):
    """Libros con la palabra sin tilde en algún texto que no sea técnico (ruta, slug, nombre propio)."""
    pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
    return [b['id'] for b in books
            if any(pattern.search(text) and not tildes.is_technical_use(text, word) for text in strings(b))]


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
        self.assertEqual(found, [], '\n'.join(found[:40]))


class CulpritRule(unittest.TestCase):
    def test_names_the_book_whose_text_lacks_the_accent(self):
        books = [{'id': 'isbn-1', 'titulo': 'Un clásico', 'subtitulo': 'Edición en frances'},
                 {'id': 'isbn-2', 'titulo': 'Cartas', 'autores': ['Frances Burney']},
                 {'id': 'isbn-3', 'titulo': 'Otro', 'url': 'https://x.es/frances-libro'}]
        self.assertEqual(culprits('frances', books), ['isbn-1'])


if __name__ == '__main__':
    unittest.main()
