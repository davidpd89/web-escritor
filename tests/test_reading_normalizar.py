"""La normalización reescribe lo reparable en vez de parar la carga, y no toca lo que ya está bien."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reading_normalizar as n  # noqa: E402


def libro(**campos):
    return {'id': 'isbn-9788498382372', 'titulo': 'Coraline', 'autores': ['Neil Gaiman'], 'isbn13': '9788498382372',
            'descripcion_breve': 'Tras mudarse a una casa antigua, Coraline encuentra una puerta.', **campos}


class NormalizarTest(unittest.TestCase):
    def prueba(self, campo, valor, esperado):
        b = libro(**{campo: valor})
        self.assertGreater(n.normalizar([b]), 0)
        self.assertEqual(b[campo], esperado)
        self.assertEqual(n.normalizar([b]), 0, 'idempotente')

    def test_autor_en_mayusculas(self):
        self.prueba('autores', ['JØRN LIER HORST'], ['Jørn Lier Horst'])

    def test_autor_string_y_repetidos(self):
        self.prueba('autores', 'Ana Gil', ['Ana Gil'])
        self.prueba('autores', ['Ana Gil', 'Ana Gil'], ['Ana Gil'])

    def test_mojibake_con_vocal_mayuscula(self):
        # «Á» llega como Ã + U+0081, que cp1252 no codifica.
        sucio = 'José Ángel Mañas'.encode('utf-8').decode('latin-1')
        self.prueba('autores', [sucio], ['José Ángel Mañas'])
        self.prueba('titulo', sucio, 'José Ángel Mañas')

    def test_titulo_con_html_y_espacios(self):
        self.prueba('titulo', '  <b>Coraline</b> &amp;  otros\n', 'Coraline & otros')

    def test_titulo_largo(self):
        b = libro(titulo='Manual completo: ' + 'historia universal de las ideas ' * 12)
        n.normalizar([b])
        self.assertEqual(b['titulo'], 'Manual completo')
        b = libro(titulo='palabra ' * 60)
        n.normalizar([b])
        self.assertLessEqual(len(b['titulo']), 200)

    def test_ligaduras(self):
        self.prueba('titulo', 'Un ﬁn ﬂamante', 'Un fin flamante')

    def test_isbn_y_fechas_y_urls(self):
        self.prueba('isbn13', '978-84-9838-237-2', '9788498382372')
        self.prueba('isbn13', 9788498382372, '9788498382372')
        self.prueba('fecha_publicacion', '23/11/2026', '2026-11-23')
        self.prueba('fecha_publicacion', 20261123, '2026-11-23')
        self.prueba('portada_fuente_url', 'http://example.com/a.jpg', 'https://example.com/a.jpg')

    def test_sinopsis_gritada_html_y_larga(self):
        b = libro(descripcion_breve='<p>' + 'UNA NOVELA QUE LO CAMBIA TODO. ' * 4 + '</p>')
        n.normalizar([b])
        self.assertNotIn('<', b['descripcion_breve'])
        self.assertNotEqual(b['descripcion_breve'], b['descripcion_breve'].upper())
        b = libro(descripcion_breve='Frase corta. ' * 300)
        n.normalizar([b])
        self.assertLessEqual(len(b['descripcion_breve']), 1200)

    def test_lo_irreparable_no_se_inventa(self):
        b = libro(titulo='', autores=[''], isbn13='12345', fecha_publicacion='2026-13-45')
        antes = copy.deepcopy(b)
        n.normalizar([b])
        self.assertEqual(b, antes)

    def test_parrafos_de_la_sinopsis_se_conservan(self):
        texto = 'Primer párrafo con texto suficiente.\n\nSegundo párrafo con más texto.'
        b = libro(sinopsis_completa=texto)
        self.assertEqual(n.normalizar([b]), 0)
        self.assertEqual(b['sinopsis_completa'], texto)

    def test_el_catalogo_real_apenas_cambia(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        libros = copy.deepcopy(data['libros'][::10])
        cambios = n.normalizar(libros)
        self.assertLessEqual(cambios, len(libros) * 0.02, 'la normalización no debe reescribir lo ya publicado')
        self.assertEqual(n.normalizar(libros), 0, 'idempotente sobre datos reales')


if __name__ == '__main__':
    unittest.main()
