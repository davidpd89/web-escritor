"""R5-1: el sitio tiene presupuesto (Pages 1 GB) y la carga nocturna lo respeta (fable-direccion-2026-11-18 §2.0)."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import presupuesto_sitio as ps  # noqa: E402

spec = importlib.util.spec_from_file_location('refresh_presupuesto', ROOT / 'scripts/refresh-reading-catalogue.py')
refresh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refresh)
MB = 1024 * 1024


class Medir(unittest.TestCase):
    def test_measures_bytes_files_and_folders_and_cost_per_published_book(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist = Path(tmp)
            (dist / 'libro').mkdir()
            (dist / 'libro/a.html').write_bytes(b'x' * 300)
            (dist / 'libro/b.html').write_bytes(b'x' * 500)
            (dist / 'index.html').write_bytes(b'x' * 200)
            catalogo = {'libros': [{'estado': 'publicado'}, {'estado': 'publicado'}, {'estado': 'borrador'}]}
            medida = ps.medir(dist, catalogo)
        self.assertEqual(medida['bytes'], 1000)
        self.assertEqual(medida['ficheros'], 3)
        self.assertEqual(medida['por_carpeta'], {'libro': 800, '.': 200})
        self.assertEqual(medida['libros'], 2)
        self.assertEqual(medida['coste_por_libro'], 500)

    def test_over_900_mb_fails_before_upload(self):
        self.assertTrue(ps.comprobar({'bytes': 901 * MB}))
        self.assertEqual(ps.comprobar({'bytes': 899 * MB}), [])


class AltasMax(unittest.TestCase):
    medida = {'bytes': 700 * MB, 'libros': 1000, 'coste_por_libro': MB // 10}

    def test_without_tope_only_space_limits_the_day(self):
        # 700 MB medidos: quedan 150 MB = 1500 libros, hechas o no hoy.
        self.assertEqual(ps.altas_max(self.medida, libros_ahora=1000, hechas_hoy=0), 1500)
        self.assertEqual(ps.altas_max(self.medida, libros_ahora=1000, hechas_hoy=900), 1500)

    def test_optional_tope_minus_what_is_already_done(self):
        self.assertEqual(ps.altas_max(self.medida, libros_ahora=1000, hechas_hoy=0, tope=250), 250)
        self.assertEqual(ps.altas_max(self.medida, libros_ahora=1000, hechas_hoy=200, tope=250), 50)
        self.assertEqual(ps.altas_max(self.medida, libros_ahora=1000, hechas_hoy=300, tope=250), 0)

    def test_tope_comes_from_env_and_zero_or_garbage_means_none(self):
        self.assertEqual(ps.tope_dia({'READING_TOPE_ALTAS_DIA': '250'}), 250)
        for valor in ('', '0', '-3', 'mucho'):
            self.assertIsNone(ps.tope_dia({'READING_TOPE_ALTAS_DIA': valor}))
        self.assertIsNone(ps.tope_dia({}))

    def test_room_left_under_850_mb_caps_the_night(self):
        # 840 MB medidos: quedan 10 MB = 100 libros.
        medida = dict(self.medida, bytes=840 * MB)
        self.assertEqual(ps.altas_max(medida, libros_ahora=1000, hechas_hoy=0), 100)

    def test_books_added_since_the_measurement_count_against_the_budget(self):
        medida = dict(self.medida, bytes=840 * MB)
        self.assertEqual(ps.altas_max(medida, libros_ahora=1060, hechas_hoy=0), 40)
        self.assertEqual(ps.altas_max(medida, libros_ahora=1200, hechas_hoy=0), 0)

    def test_no_measurement_means_no_new_books(self):
        self.assertEqual(ps.altas_max(None, libros_ahora=10, hechas_hoy=0), 0)
        self.assertEqual(ps.altas_max({'bytes': 1, 'libros': 0, 'coste_por_libro': 0}, libros_ahora=10, hechas_hoy=0), 0)



class MedidaYRegistro(unittest.TestCase):
    """Un artefacto o un registro estropeados no tumban la carga: sin medida legible no hay altas."""

    def test_unreadable_or_incomplete_measurement_is_no_measurement(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'm.json'
            for texto in ('{roto', '[]', '{"bytes": 1, "libros": 2}', '{"bytes": "1", "libros": 2, "coste_por_libro": 3}',
                          '{"bytes": -1, "libros": 2, "coste_por_libro": 3}'):
                with self.subTest(texto):
                    path.write_text(texto, encoding='utf-8')
                    self.assertIsNone(ps.leer_medida(path))
            path.write_text('{"bytes": 1, "libros": 2, "coste_por_libro": 3}', encoding='utf-8')
            self.assertEqual(ps.leer_medida(path)['coste_por_libro'], 3)

    def test_ultima_medida_skips_a_broken_artifact_and_takes_the_next(self):
        llamadas = []

        def fake(cmd, **kw):
            llamadas.append(cmd)
            if cmd[:3] == ['gh', 'run', 'list']:
                return type('R', (), {'stdout': '[{"databaseId": 11}, {"databaseId": 22}]', 'returncode': 0})()
            destino = Path(cmd[cmd.index('-D') + 1]) / f'{ps.ARTEFACTO}.json'
            destino.write_text('{roto' if cmd[3] == '11' else '{"bytes": 5, "libros": 1, "coste_por_libro": 5}',
                               encoding='utf-8')
            return type('R', (), {'stdout': '', 'returncode': 0})()
        with patch.object(ps.subprocess, 'run', fake):
            self.assertEqual(ps.ultima_medida()['bytes'], 5)
        self.assertIn('completed', llamadas[0], 'un despliegue fallido por tamaño también trae medida')

    def test_ultima_medida_without_gh_or_any_download_is_no_measurement(self):
        def sin_gh(cmd, **kw):
            raise FileNotFoundError('gh')
        with patch.object(ps.subprocess, 'run', sin_gh):
            self.assertIsNone(ps.ultima_medida())

        def descarga_falla(cmd, **kw):
            if cmd[:3] == ['gh', 'run', 'list']:
                return type('R', (), {'stdout': '[{"databaseId": 11}, {"databaseId": 22}]', 'returncode': 0})()
            if cmd[3] == '11':
                raise ps.subprocess.TimeoutExpired(cmd, 120)
            return type('R', (), {'stdout': '', 'returncode': 1})()
        with patch.object(ps.subprocess, 'run', descarga_falla):
            self.assertIsNone(ps.ultima_medida())

    def test_anotar_never_leaves_a_half_written_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            ps.anotar(tmp, '2026-11-01', 3)
            with patch.object(ps.os, 'replace', side_effect=OSError('corte')):
                with self.assertRaises(OSError):
                    ps.anotar(tmp, '2026-11-01', 2)
            self.assertEqual(ps._ledger(tmp), {'2026-11-01': 3})

    def test_malformed_ledger_counts_as_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ps.LEDGER
            for texto in ('{roto', '[1, 2]', '"x"'):
                with self.subTest(texto):
                    path.write_text(texto, encoding='utf-8')
                    self.assertEqual(ps._ledger(tmp), {})
            path.write_text('{"2026-11-01": 3, "2026-11-02": "x", "2026-11-03": -1, "2026-11-04": true}',
                            encoding='utf-8')
            self.assertEqual(ps._ledger(tmp), {'2026-11-01': 3})
            ps.anotar(tmp, '2026-11-01', 2)
            self.assertEqual(ps._ledger(tmp), {'2026-11-01': 5})

    def test_anotar_keeps_only_the_last_14_days(self):
        with tempfile.TemporaryDirectory() as tmp:
            for dia in range(1, 21):
                ps.anotar(tmp, f'2026-11-{dia:02d}', dia)
            ledger = ps._ledger(tmp)
            self.assertEqual(sorted(ledger), [f'2026-11-{d:02d}' for d in range(7, 21)])
            self.assertEqual(ledger['2026-11-20'], 20)


class CargaSinPresupuesto(unittest.TestCase):
    def run_intake(self, cupo, nuevos=()):
        config = {'amazon_catalogo': {'enabled': True, 'altas': 1000, 'peticiones': 600}}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work = root / 'w'
            work.mkdir()
            (root / 'data').mkdir()
            cat = root / 'data/reading-catalogue.json'
            cat.write_text(json.dumps({'libros': [{'id': 'a', 'estado': 'publicado'}]}), encoding='utf-8')
            fake = type(sys)('catalogo_amazon')
            fake.WORK = work
            calls = []

            def main(argv):
                calls.append(argv)
                data = json.loads(cat.read_text(encoding='utf-8'))
                data['libros'] += [{'id': n, 'estado': 'publicado'} for n in nuevos]
                cat.write_text(json.dumps(data), encoding='utf-8')
                return 0
            fake.main = main
            with patch.dict(sys.modules, {'catalogo_amazon': fake}), \
                 patch.object(refresh, 'ROOT', root), \
                 patch.object(refresh.estado, 'restaurar'), \
                 patch.object(refresh.estado, 'WORK', work), \
                 patch.object(refresh.presupuesto, 'cupo_de_hoy', return_value=cupo), \
                 patch.object(refresh, 'write_if_changed'):
                report = refresh.amazon_intake(config, publish=True)
                ledger = json.loads((work / ps.LEDGER).read_text(encoding='utf-8')) if (work / ps.LEDGER).exists() else {}
        return report, calls, ledger

    def test_zero_budget_skips_new_books_and_ends_degraded_not_failed(self):
        report, calls, _ = self.run_intake(0)
        self.assertEqual(calls, [])
        self.assertEqual(report['stats']['accepted'], 0)
        self.assertEqual(report['stats']['degradada'], 'presupuesto')
        self.assertNotIn('error', report['stats'])

    def test_budget_caps_the_altas_argument_and_records_the_night(self):
        report, calls, ledger = self.run_intake(30, nuevos=['b', 'c'])
        argv = calls[0]
        self.assertEqual(argv[argv.index('--altas') + 1], '30')
        self.assertEqual(report['stats']['accepted'], 2)
        self.assertEqual(sum(ledger.values()), 2)

    def test_ledger_is_persisted_with_the_load_state(self):
        self.assertIn(ps.LEDGER, refresh.estado.FILES)


if __name__ == '__main__':
    unittest.main()
