"""Detector de duplicados del catálogo: avisa de lo que es el mismo libro y calla ante series y ediciones. Sin red."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import catalogo_duplicados as d  # noqa: E402


def libro(ident, titulo, autor='Ana Pérez', formato='tapa-blanda', editorial='sello', **extra):
    return dict({'id': f'isbn-{ident}', 'isbn13': str(ident), 'slug': f'libro-{ident}', 'titulo': titulo,
                 'autores': [autor], 'formato_edicion': formato, 'editorial_slug': editorial, 'estado': 'publicado'}, **extra)


def clases(libros):
    return sorted(h['clase'] for h in d.buscar(libros)[0])


class NormalizarTests(unittest.TestCase):
    def test_tildes_signos_y_mayusculas_no_cuentan(self):
        self.assertEqual(d.normalizar('¡El Señor  de los Anillos!'), 'el senor de los anillos')
        self.assertEqual(d.normalizar(None), '')

    def test_el_orden_del_nombre_del_autor_no_cuenta(self):
        self.assertEqual(d.clave_autor({'autores': ['Gaiman, Neil']}), d.clave_autor({'autores': ['Neil Gaiman']}))
        self.assertEqual(d.clave_autor({'autores': []}), '')
        self.assertEqual(d.clave_autor({'autores': 'Neil Gaiman'}), 'gaiman neil')


class BuscarTests(unittest.TestCase):
    def test_mismo_libro_con_dos_isbn_se_avisa_con_sus_ids(self):
        hallazgos, _ = d.buscar([libro(1, 'Coraline'), libro(2, 'CORALINE')])
        self.assertEqual([h['clase'] for h in hallazgos], ['misma_edicion'])
        self.assertEqual(hallazgos[0]['ids'], ['isbn-1', 'isbn-2'])

    def test_una_errata_en_el_titulo_se_avisa(self):
        self.assertEqual(clases([libro(1, 'La sombra del viento'), libro(2, 'La sombra del veinto')]), ['titulo_parecido'])

    def test_el_mismo_titulo_con_subtitulo_se_avisa(self):
        self.assertEqual(clases([libro(1, 'Cartas de Ciudad Reloj'), libro(2, 'Cartas de Ciudad Reloj: una novela')]),
                         ['titulo_parecido'])

    def test_espacios_en_otro_sitio_se_avisa(self):
        self.assertEqual(clases([libro(1, 'Los superhéroes de la cocina'), libro(2, 'Los super héroes de la cocina')]),
                         ['titulo_parecido'])

    def test_los_tomos_de_una_serie_no_son_duplicados(self):
        self.assertEqual(clases([libro(1, 'El pop-rock de los 60 - Capítulo III'), libro(2, 'El pop-rock de los 60 - Capítulo V'),
                                 libro(3, 'Una enfermedad llamada amor 18'), libro(4, 'Una enfermedad llamada amor 19'),
                                 libro(5, 'Murdoku (edición especial)'), libro(6, 'Murdoku 2 (edición especial)'),
                                 libro(7, 'Crónicas de la torre'), libro(8, 'Crónicas de la torre 2')]), [])

    def test_dos_obras_con_titulo_de_coleccion_no_son_duplicados(self):
        self.assertEqual(clases([libro(1, 'Ilíada: Ediciones icónicas (Penguin Clásicos)'),
                                 libro(2, 'Odisea: Ediciones icónicas (Penguin Clásicos)')]), [])

    def test_otra_edicion_de_la_misma_obra_se_cuenta_y_no_se_lista(self):
        hallazgos, ediciones = d.buscar([libro(1, 'Coraline'), libro(2, 'Coraline', formato='tapa-dura'),
                                         libro(3, 'Coraline', editorial='otro-sello')])
        self.assertEqual((hallazgos, ediciones), ([], 3))

    def test_paginas_idioma_o_marca_de_edicion_distintos_son_otro_producto(self):
        # Los 7 hallazgos de la primera revisión (16/11) eran de esta clase: no deben volver a salir.
        casos = [
            [libro(1, 'Dinosaurios', numero_paginas=64), libro(2, 'Dinosaurios', numero_paginas=24)],
            [libro(1, 'El día de la Trilla (Empíreo) Edición limitada con cantos tintados'), libro(2, 'El día de la Trilla (Empíreo)')],
            [libro(1, 'Orgullo y prejuicio (ED. Especial)'), libro(2, 'Orgullo y prejuicio')],
            [libro(1, '¿Hay conciencia en tu cerebro?'), libro(2, '¿Hay conciencia en tu cerebro? / Is There Consciousness in Your Brain?')],
            [libro(1, 'Rebeldes', idioma='es'), libro(2, 'Rebeldes', idioma='ca')],
        ]
        for libros in casos:
            with self.subTest(titulo=libros[0]['titulo']):
                hallazgos, ediciones = d.buscar(libros)
                self.assertEqual((hallazgos, ediciones), ([], 1))

    def test_sin_dato_de_paginas_o_idioma_sigue_avisando(self):
        self.assertEqual(clases([libro(1, 'Dinosaurios', numero_paginas=64), libro(2, 'Dinosaurios')]), ['misma_edicion'])
        self.assertEqual(clases([libro(1, 'Dinosaurios', numero_paginas=64, idioma='es'),
                                 libro(2, 'Dinosaurios', numero_paginas=64, idioma='es')]), ['misma_edicion'])

    def test_autores_distintos_no_se_comparan(self):
        self.assertEqual(clases([libro(1, 'Dinosaurios'), libro(2, 'Dinosaurios', autor='Luis Gil')]), [])

    def test_isbn_y_slug_repetidos(self):
        hallazgos, _ = d.buscar([libro(1, 'Uno'), libro(1, 'Otro', autor='Luis Gil'), libro(3, 'Tres', slug='libro-1')])
        self.assertEqual({h['clase']: h['ids'] for h in hallazgos},
                         {'isbn_repetido': ['isbn-1', 'isbn-1'], 'slug_repetido': ['isbn-1', 'isbn-1', 'isbn-3']})

    def test_un_libro_defectuoso_no_rompe_la_revision(self):
        raros = [{'id': 'a'}, {'id': 'b', 'titulo': None, 'autores': None}, {'id': 'c', 'titulo': '', 'autores': ['']},
                 libro(1, 'Coraline')]
        self.assertEqual(d.buscar(raros), ([], 0))


class SalidaTests(unittest.TestCase):
    def ejecutar(self, libros, *args):
        with tempfile.TemporaryDirectory() as carpeta:
            catalogo, salida, datos = (Path(carpeta) / n for n in ('c.json', 'i.md', 'd.json'))
            catalogo.write_text(json.dumps({'libros': libros}), encoding='utf-8')
            codigo = d.main(['--catalogo', str(catalogo), '--salida', str(salida), '--json', str(datos), *args])
            return codigo, salida.read_text(encoding='utf-8'), json.loads(datos.read_text(encoding='utf-8'))

    def test_el_informe_nombra_los_ids_y_no_tumba_nada(self):
        codigo, texto, datos = self.ejecutar([libro(1, 'Coraline'), libro(2, 'Coraline')])
        self.assertEqual(codigo, 0)
        self.assertIn('`isbn-1`, `isbn-2`', texto)
        self.assertEqual(datos['hallazgos'][0]['ids'], ['isbn-1', 'isbn-2'])

    def test_estricto_solo_falla_por_identificadores_repetidos(self):
        self.assertEqual(self.ejecutar([libro(1, 'Coraline'), libro(2, 'Coraline')], '--estricto')[0], 0)
        self.assertEqual(self.ejecutar([libro(1, 'Uno'), libro(1, 'Otro', autor='Luis Gil')], '--estricto')[0], 1)

    def test_catalogo_limpio(self):
        codigo, texto, _ = self.ejecutar([libro(1, 'Uno'), libro(2, 'Dos')])
        self.assertEqual(codigo, 0)
        self.assertIn('Ningún duplicado sospechoso', texto)


if __name__ == '__main__':
    unittest.main()
