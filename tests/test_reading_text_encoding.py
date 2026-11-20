"""Contrato de datos: ningún texto de un libro publicado trae mojibake o caracteres de sustitución.

Origen (19/11): la carga publicó «El origen de los Âsanas» (la fuente trajo la Á rota) y la puerta de la PR
(scripts/check-public-text-encoding.py, que mira el HTML) la dejó en rojo; la carga entera quedó sin fusionar.
La puerta de datos no miraba el texto de los libros, así que no podía apartar solo ese libro. Usa la misma lista
de señales que la puerta pública: lo que aquella rechazaría aquí aparta el libro, no el lote."""
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from contrato_libros import incumplen  # noqa: E402

_spec = importlib.util.spec_from_file_location('check_public_text_encoding', ROOT / 'scripts/check-public-text-encoding.py')
encoding = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(encoding)


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from strings(item)


def suspicious(book):
    return {token for text in strings(book) for token in encoding.MOJIBAKE if token in text}


class ReadingTextEncodingTest(unittest.TestCase):
    def test_published_books_have_no_mojibake(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        bad = {b['id']: 'texto con señales de codificación rota: ' + ' '.join(sorted(map(ascii, found)))
               for b in data['libros'] if b.get('estado') == 'publicado' and (found := suspicious(b))}
        incumplen('texto sin mojibake', bad)

    def test_detector_sees_the_known_cases(self):
        self.assertTrue(suspicious({'titulo': 'El origen de los Âsanas'}))
        self.assertTrue(suspicious({'autores': ['Ana �']}))
        self.assertFalse(suspicious({'titulo': 'El origen de los Ásanas', 'autores': ['Isabel Hernández']}))


if __name__ == '__main__':
    unittest.main()
