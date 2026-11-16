"""Qué cambios de main obligan a regenerar los artefactos de una PR antes de fusionarla."""
import importlib.util
import json
import unittest
from pathlib import Path
from unittest import mock

spec = importlib.util.spec_from_file_location('publicacion_entradas',
                                              Path(__file__).resolve().parents[1] / 'scripts/publish-radar-refresh.py')
publication = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publication)


def compare(files, ahead=1):
    return mock.patch.object(publication, 'gh', lambda *a: json.dumps({'ahead_by': ahead, 'files': files}))


class MainCambioEntradas(unittest.TestCase):
    def test_al_dia_no_pide_nada(self):
        with compare([{'filename': 'data/reading-catalogue.json'}], ahead=0):
            self.assertEqual(publication.main_cambio_entradas('o/r', 's'), [])

    def test_una_pagina_retirada_por_renombrado_cuenta(self):
        """CodeRabbit #1320: index.html -> index.html.bak solo traía el destino, que no es entrada de nadie."""
        files = [{'filename': 'recomendaciones/libros/x/index.html.bak', 'status': 'renamed',
                  'previous_filename': 'recomendaciones/libros/x/index.html'}]
        with compare(files):
            self.assertEqual(publication.main_cambio_entradas('o/r', 's'), ['recomendaciones/libros/x/index.html'])

    def test_lista_truncada_por_la_api_no_descarta_nada(self):
        files = [{'filename': f'otros/{i}.txt'} for i in range(300)]
        with compare(files):
            self.assertEqual(publication.main_cambio_entradas('o/r', 's')[-1], '…')

    def test_un_script_que_no_alimenta_a_los_builders_no_regenera(self):
        """16/11: main tocó scripts/reading-texts.py durante la CI de #1419 y el glob scripts/reading*.py lo
        contaba como entrada de los builders, así que la publicación moría con StaleMerge sin motivo. El barrido de
        textos, el radar de Amazon, Telegram, la cuarentena… no los importa ningún builder: no cambian lo generado."""
        for ajeno in ('scripts/reading-texts.py', 'scripts/reading_telegram.py', 'scripts/reading_amazon_radar.py',
                      'scripts/reading_quarantine.py', 'scripts/reading_intake_pipeline.py'):
            self.assertFalse(publication.entrada_de_builders(ajeno), ajeno)
            with compare([{'filename': ajeno}]):
                self.assertEqual(publication.main_cambio_entradas('o/r', 's'), [], ajeno)

    def test_un_auxiliar_real_de_los_builders_si_regenera(self):
        """El reverso del mismo fallo: auxiliares que los builders sí importan y el glob se saltaba (genre_families,
        site_clock, arbol_publicado) han de contar; si no, un cambio de main en ellos fusiona artefactos desfasados."""
        for entrada in ('scripts/reading_taxonomy.py', 'scripts/reading_publisher_links.py',
                        'scripts/reading_intake_core.py', 'scripts/genre_families.py', 'scripts/site_clock.py',
                        'scripts/arbol_publicado.py', 'data/reading-catalogue.json'):
            self.assertTrue(publication.entrada_de_builders(entrada), entrada)
            with compare([{'filename': entrada}]):
                self.assertEqual(publication.main_cambio_entradas('o/r', 's'), [entrada], entrada)


if __name__ == '__main__':
    unittest.main()
