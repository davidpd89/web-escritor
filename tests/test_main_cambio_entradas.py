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


if __name__ == '__main__':
    unittest.main()
