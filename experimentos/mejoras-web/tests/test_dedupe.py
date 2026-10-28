import unittest
import util  # noqa
import dedupe


class Dedupe(unittest.TestCase):
    A = {"id": "1", "titulo": "Skip link", "necesidad": "Los lectores con teclado no pueden saltar al contenido principal de la pagina", "criterio": "enlace skip-link visible al enfocar", "archivos": ["index.html"]}

    def test_misma_necesidad_con_otras_palabras_y_otra_fuente(self):
        b = {"id": "2", "titulo": "Saltar bloques", "necesidad": "Un lector que navega con teclado no puede saltar directamente al contenido principal", "criterio": "skip link con foco visible", "archivos": ["index.html", "styles.css"]}
        d = dedupe.buscar_duplicado(self.A, [b])
        self.assertIsNotNone(d); self.assertEqual(d[0], "2")

    def test_misma_url_distinta_necesidad_no_es_duplicado(self):
        c = {"id": "3", "titulo": "Calendario ICS", "necesidad": "Mostrar las fechas de ferias en un calendario descargable ICS para suscribirse", "criterio": "archivo ics valido", "archivos": ["ferias.html"]}
        self.assertIsNone(dedupe.buscar_duplicado(self.A, [c]))

    def test_mismo_comportamiento_mismos_archivos_y_criterio(self):
        b = {"id": "4", "titulo": "Otro titulo", "necesidad": "Navegacion rapida para personas con discapacidad motriz sin raton en la portada",
             "criterio": "enlace skip-link visible al enfocar", "archivos": ["index.html"]}
        d = dedupe.buscar_duplicado(self.A, [b])
        self.assertIsNotNone(d); self.assertIn("comportamiento", d[1])

    def test_huella_exacta_y_no_se_compara_consigo_mismo(self):
        h = dedupe.huella_necesidad(self.A["necesidad"])
        self.assertEqual(dedupe.buscar_duplicado(self.A, [{**self.A, "h_necesidad": h}]), None)  # mismo id
        r = dedupe.buscar_duplicado(self.A, [{"id": "9", "h_necesidad": h, "necesidad": "x"}])
        self.assertEqual(r[0], "9"); self.assertEqual(r[2], 1.0)

    def test_acentos_plurales_y_stopwords(self):
        self.assertEqual(dedupe.conceptos("Filtros de búsqueda"), dedupe.conceptos("filtro  busqueda"))


if __name__ == "__main__":
    unittest.main()
