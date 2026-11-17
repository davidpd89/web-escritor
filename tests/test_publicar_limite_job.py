"""Límite común del job para el publicador (scripts/publish-radar-refresh.py: limite_del_job).

Clase de fallo: atlas-directory-sync cancelado por timeout (09/11, 16/11) esperando a la carga en un segundo intento
con presupuesto nuevo. Todo job que publica fija PUBLICAR_HASTA y el publicador recorta sus esperas a ese límite.
"""
import importlib.util
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publication', ROOT / 'scripts/publish-radar-refresh.py')
publication = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publication)
PUBLICA = re.compile(r'scripts/(refresh-atlas-directory|refresh-reading-catalogue)\.py --publish'
                     r'|scripts/publish-(radar|reading)-refresh\.py')
MARGEN = 10


class LimiteDelJob(unittest.TestCase):
    def test_sin_variable_no_hay_limite(self):
        self.assertIsNone(publication.limite_del_job({}))
        self.assertEqual(publication.recortar_al_job(500.0, {}), 500.0)

    def test_convierte_epoch_a_reloj_monotono(self):
        self.assertEqual(publication.limite_del_job({'PUBLICAR_HASTA': '1600'}, ahora=1000, reloj=50), 650)

    def test_recorta_un_presupuesto_nuevo(self):
        """El segundo intento pide 90 min, pero al job le quedan 5: manda el límite del job."""
        import time
        hasta = str(time.time() + 300)
        recortado = publication.recortar_al_job(time.monotonic() + 5400, {'PUBLICAR_HASTA': hasta})
        self.assertLess(recortado - time.monotonic(), 301)

    def test_esperar_escritores_suelta_al_llegar_al_limite(self):
        original = publication.gh
        publication.gh = lambda *a: '[{"databaseId": 1}]'
        try:
            with self.assertRaises(TimeoutError):
                publication.esperar_escritores(('reading-catalogue-sync.yml',), 0, poll=0)
        finally:
            publication.gh = original


class WorkflowsQuePublican(unittest.TestCase):
    def test_fijan_el_limite_antes_de_publicar(self):
        vistos = []
        for wf in sorted((ROOT / '.github/workflows').glob('*.yml')):
            datos = yaml.safe_load(wf.read_text(encoding='utf-8')) or {}
            for nombre, job in (datos.get('jobs') or {}).items():
                pasos = job.get('steps') or []
                publica = [i for i, p in enumerate(pasos) if PUBLICA.search(str(p.get('run', '')))]
                if not publica:
                    continue
                vistos.append(f'{wf.name}:{nombre}')
                fija = [i for i, p in enumerate(pasos) if 'PUBLICAR_HASTA=' in str(p.get('run', ''))]
                self.assertTrue(fija and fija[0] < publica[0], f'{wf.name}:{nombre} publica sin PUBLICAR_HASTA')
                minutos = int(re.search(r'\+ (\d+) \* 60', pasos[fija[0]]['run']).group(1))
                self.assertEqual(minutos, int(job['timeout-minutes']) - MARGEN,
                                 f'{wf.name}:{nombre}: PUBLICAR_HASTA debe ser timeout-minutes - {MARGEN}')
        self.assertGreaterEqual(len(vistos), 3, vistos)


if __name__ == '__main__':
    unittest.main()
