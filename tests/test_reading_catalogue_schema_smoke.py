"""Esquema mínimo de cada libro publicado (schemas/reading-catalogue/libro-v1.schema.json).

Entra solo en la puerta de datos de la carga por el patrón `test_*_smoke.py` de scripts/check-reading-data.py. El
mensaje nombra los ids que fallan: la cuarentena (reading_quarantine.flagged_books) los aparta y el resto del lote
sigue. Solo se miran los publicados; un borrador incompleto no debe parar la carga cada noche.

La carga no instala `jsonschema`, así que el subconjunto que usa el esquema (type, required, properties, pattern,
enum, minLength, minItems, items) se valida aquí. Si el esquema usa otra palabra clave, el test lo dice en vez de
ignorarla. Con `jsonschema` instalado, se comprueba además que los dos validadores coinciden.
"""
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from contrato_libros import incumplen  # noqa: E402
SCHEMA = json.loads((ROOT / 'schemas/reading-catalogue/libro-v1.schema.json').read_text(encoding='utf-8'))
KEYWORDS = {'$schema', '$id', 'title', 'description', 'type', 'required', 'properties', 'pattern', 'enum',
            'minLength', 'minItems', 'items'}
TYPES = {'string': str, 'array': list, 'object': dict, 'integer': int, 'boolean': bool}


def unsupported(schema, path='$'):
    """Palabras clave que este validador no sabe aplicar (no deben pasar en silencio)."""
    out = [f'{path}.{k}' for k in schema if k not in KEYWORDS]
    for name, sub in schema.get('properties', {}).items():
        out += unsupported(sub, f'{path}.{name}')
    if 'items' in schema:
        out += unsupported(schema['items'], f'{path}[]')
    return out


def errors(value, schema, path=''):
    if 'type' in schema:
        expected = TYPES[schema['type']]
        if not isinstance(value, expected) or (expected is int and isinstance(value, bool)):
            return [f'{path or "libro"}: se esperaba {schema["type"]}']
    out = []
    if 'enum' in schema and value not in schema['enum']:
        out.append(f'{path}: {value!r} fuera de {schema["enum"]}')
    if isinstance(value, str):
        if len(value) < schema.get('minLength', 0):
            out.append(f'{path}: vacío o demasiado corto')
        if 'pattern' in schema and not re.search(schema['pattern'], value):
            out.append(f'{path}: {value[:40]!r} no cumple {schema["pattern"]}')
    if isinstance(value, list):
        if len(value) < schema.get('minItems', 0):
            out.append(f'{path}: lista vacía')
        for i, item in enumerate(value):
            out += errors(item, schema.get('items', {}), f'{path}[{i}]')
    if isinstance(value, dict):
        out += [f'falta {key}' for key in schema.get('required', ()) if key not in value]
        for key, sub in schema.get('properties', {}).items():
            if key in value:
                out += errors(value[key], sub, key)
    return out


class ValidatorTest(unittest.TestCase):
    GOOD = {'id': 'isbn-9788498382372', 'isbn13': '9788498382372', 'titulo': 'T', 'autores': ['A'], 'slug': 't-1',
            'estado': 'publicado', 'formato_edicion': 'tapa-blanda', 'editorial': 'E', 'idioma': 'es',
            'portada_local': '/assets/reading-covers/x.webp', 'fecha_publicacion': '2026-11-16'}

    def test_schema_only_uses_supported_keywords(self):
        self.assertEqual(unsupported(SCHEMA), [])

    def test_good_book_passes(self):
        self.assertEqual(errors(self.GOOD, SCHEMA), [])

    def test_each_kind_of_breakage_is_caught(self):
        cases = {'isbn13': '978849838237', 'autores': [], 'slug': 'Con Mayúsculas', 'estado': 'retirado',
                 'formato_edicion': 'rustica', 'titulo': '   ', 'portada_local': 'https://x/y.jpg',
                 'fecha_publicacion': '16/11/2026'}
        for key, bad in cases.items():
            with self.subTest(key=key):
                self.assertTrue(errors({**self.GOOD, key: bad}, SCHEMA))
        missing = dict(self.GOOD)
        del missing['editorial']
        self.assertIn('falta editorial', errors(missing, SCHEMA))
        self.assertTrue(errors({**self.GOOD, 'autores': 'Una cadena'}, SCHEMA))

    def test_agrees_with_jsonschema_when_installed(self):
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.skipTest('jsonschema no instalado (la carga no lo necesita)')
        Draft202012Validator.check_schema(SCHEMA)
        validator = Draft202012Validator(SCHEMA)
        for book in (self.GOOD, {**self.GOOD, 'slug': 'Mal'}, {**self.GOOD, 'autores': []}):
            self.assertEqual(validator.is_valid(book), not errors(book, SCHEMA), book)


class PublishedBooksMatchSchemaTest(unittest.TestCase):
    def test_every_published_book_matches_the_schema(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        bad = {}
        for book in data['libros']:
            if book.get('estado') == 'publicado':
                found = errors(book, SCHEMA)
                if found:
                    bad[book.get('id', '?')] = found
        # Un id por línea, al principio: así lo lee la cuarentena y el resto del lote sigue.
        incumplen('ficha conforme al esquema', {book_id: '; '.join(e) for book_id, e in bad.items()})


if __name__ == '__main__':
    unittest.main()
