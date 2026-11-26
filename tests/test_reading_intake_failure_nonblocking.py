"""Un fallo de las altas de Amazon no deja la noche sin precios ni portadas (run 42572925804, 09/11/2026).

refresh() abortaba en amazon_intake antes de market_refresh: ni precios ni cambio de portadas por la API.
"""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('refresh_nonblocking', ROOT / 'scripts/refresh-reading-catalogue.py')
refresh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refresh)


class IntakeFailure(unittest.TestCase):
    def run_refresh(self, intake, market_error=None, issue_error=None, price_status=None, assemble_error=None):
        config = {'autopublish': True, 'amazon_catalogo': {'enabled': True}}
        calls = MagicMock()
        with patch.object(refresh, 'read_json', return_value=config), \
             patch.object(refresh, 'reconcile_deploy'), \
             patch.object(refresh.subprocess, 'check_output', return_value=''), \
             patch.object(refresh.publisher.publication, 'gh', return_value='[]'), \
             patch.object(refresh, 'checkpoints', return_value=[]), \
             patch.object(refresh, 'amazon_intake', side_effect=intake), \
             patch.object(refresh, 'discard_intake_writes', calls.discard), \
             patch.object(refresh, 'write_if_changed'), \
             patch.object(refresh, 'market_refresh', calls.market), \
             patch.object(refresh, 'follow_main'), \
             patch.object(refresh, 'save_checkpoint', return_value='cp'), \
             patch.object(refresh, 'health_report'), \
             patch.object(refresh.estado, 'guardar', calls.guardar), \
             patch.object(refresh, 'open_issue', calls.issue), \
             patch.object(refresh, 'assemble', calls.assemble):
            calls.market.return_value = True
            calls.market.side_effect = market_error
            calls.issue.side_effect = issue_error
            calls.assemble.side_effect = assemble_error
            if price_status:
                def market(config):
                    refresh.MARKET_STATUS['precios'] = price_status  # refresh_offers devuelve el estado, no lanza
                    return True
                calls.market.side_effect = market
            try:
                refresh.refresh(publish=True)
                error = None
            except (Exception, SystemExit) as exc:  # noqa: BLE001
                error = exc
        return calls, error

    def test_failed_intake_still_refreshes_prices_and_covers_then_degrades_green(self):
        """R2-07 (GPT, 26/11): el rojo final cortaba la cadena y lanzaba un reintento de lo ya publicado."""
        def boom(config, publish):
            raise KeyError('isbn-9791388351112')
        calls, error = self.run_refresh(boom)
        calls.discard.assert_called_once()
        calls.market.assert_called_once()
        calls.assemble.assert_called_once()
        report = calls.assemble.call_args.args[0]
        self.assertEqual(report['new_books'], [])
        self.assertIn('KeyError', report['stats']['error'])
        # La cola de semillas no avanza: la noche siguiente reintenta esas altas.
        calls.guardar.assert_not_called()
        self.assertIsNone(error)
        calls.issue.assert_called_once()
        self.assertEqual(calls.issue.call_args.args[0], 'Carga degradada: altas de Amazon (KeyError)')

    def test_intake_exiting_without_credentials_does_not_stop_prices(self):
        """R2-04 (GPT, 26/11): catalogo_amazon sale con SystemExit sin credenciales; `except Exception` no lo cogía."""
        def no_credentials(config, publish):
            raise SystemExit('Faltan credenciales de Creators API')
        calls, error = self.run_refresh(no_credentials)
        self.assertIsNone(error)
        calls.discard.assert_called_once()
        calls.market.assert_called_once()
        calls.assemble.assert_called_once()
        self.assertIn('SystemExit', calls.issue.call_args.args[0])

    def test_issue_failure_does_not_turn_the_degraded_load_red(self):
        """R3-09 GPT (26/11): sin permiso o sin red para la issue, el aviso no puede tumbar lo ya publicado."""
        def boom(config, publish):
            raise KeyError('x')
        calls, error = self.run_refresh(boom, issue_error=RuntimeError('gh caído'))  # antes el mock quedaba tapado
        self.assertIsNone(error)
        calls.issue.assert_called_once()
        calls.assemble.assert_called_once()

    def test_price_provider_down_counts_as_a_failed_phase(self):
        """CodeRabbit #1595: refresh_offers no lanza con el proveedor caído; con las altas también caídas, era verde
        y el aviso decía que los precios sí se publicaron."""
        def boom(config, publish):
            raise KeyError('x')
        for status in refresh.PROVIDER_DOWN:
            with self.subTest(status=status):
                calls, error = self.run_refresh(boom, price_status=status)
                self.assertIsInstance(error, KeyError)
                bodies = ' '.join(c.args[1] for c in calls.issue.call_args_list)
                self.assertNotIn('sí se publicaron', bodies)
                calls.discard.assert_called_once()  # solo se deshacen las altas: lo guardado del mercado se queda

    def test_price_provider_down_alone_degrades_green_keeping_the_intake(self):
        calls, error = self.run_refresh(lambda config, publish: {'new_books': ['a'], 'updated_books': [], 'stats': {}},
                                        price_status='provider_unavailable')
        self.assertIsNone(error)
        self.assertEqual(calls.issue.call_args.args[0], 'Carga degradada: precios y portadas (RuntimeError)')
        calls.guardar.assert_called_once()

    def test_both_phases_failing_goes_red_with_honest_messages(self):
        """R3-12 GPT (26/11): con las dos caídas, cada aviso decía que la otra sí se publicó; y sin nada publicado, rojo
        para que entre el reintento."""
        def boom(config, publish):
            raise KeyError('x')
        calls, error = self.run_refresh(boom, market_error=TimeoutError('api'))
        self.assertIsInstance(error, KeyError)
        bodies = ' '.join(c.args[1] for c in calls.issue.call_args_list)
        self.assertEqual(calls.issue.call_count, 2)
        self.assertNotIn('sí se publicaron', bodies)

    def test_open_pr_timeout_does_not_hide_the_failed_phases(self):
        """CodeRabbit #1597: la PR que queda abierta para el siguiente cron no tapa el aviso ni el rojo de las fases."""
        def boom(config, publish):
            raise KeyError('x')
        pr = refresh.publisher.publication.PrAbierta('CI timed out; PR left open')
        calls, error = self.run_refresh(boom, assemble_error=pr)
        self.assertIs(error, pr)  # main() la convierte en aviso y conserva el punto de guardado
        self.assertEqual(calls.issue.call_args.args[0], 'Carga degradada: altas de Amazon (KeyError)')
        calls, error = self.run_refresh(boom, market_error=TimeoutError('api'), assemble_error=pr)
        self.assertIsInstance(error, KeyError)  # las dos caídas: rojo para el reintento
        self.assertEqual(calls.issue.call_count, 2)

    def test_successful_intake_keeps_the_normal_flow(self):
        calls, error = self.run_refresh(lambda config, publish: {'new_books': ['a'], 'updated_books': [], 'stats': {'accepted': 1}})
        self.assertIsNone(error)
        calls.discard.assert_not_called()
        calls.market.assert_called_once()
        calls.guardar.assert_called_once()
        calls.issue.assert_not_called()

    def test_failed_market_keeps_the_intake_and_degrades_green(self):
        """#1312 (CodeRabbit): una excepción en market_refresh salía antes de save_checkpoint y perdía las altas."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            git = lambda *a: subprocess.run(['git', *a], cwd=root, check=True, capture_output=True)
            git('init', '-q'); git('config', 'user.email', 't@t'); git('config', 'user.name', 't')
            (root / 'data').mkdir(); (root / 'assets/reading-covers').mkdir(parents=True)
            catalogue, market = root / 'data/reading-catalogue.json', root / 'assets/reading-market.json'
            catalogue.write_text('[]\n'); market.write_text('{"precios": 0}\n')
            (root / 'assets/reading-covers/vieja.webp').write_bytes(b'vieja')
            git('add', '.'); git('commit', '-qm', 'base')

            def intake(config, publish):
                catalogue.write_text('["alta"]\n')
                (root / 'assets/reading-covers/alta.webp').write_bytes(b'alta')
                return {'new_books': ['alta'], 'updated_books': [], 'stats': {'accepted': 1}}

            def market_boom(config):
                catalogue.write_text('["alta", "precio a medias"]\n')
                market.write_text('{"precios": 1}\n')
                (root / 'assets/reading-covers/precio.webp').write_bytes(b'precio')
                (root / 'assets/reading-covers/vieja.webp').unlink()
                raise TimeoutError('Creators API')

            calls = MagicMock()
            config = {'autopublish': True, 'amazon_catalogo': {'enabled': True}}
            with patch.object(refresh, 'ROOT', root), \
                 patch.object(refresh, 'read_json', return_value=config), \
                 patch.object(refresh, 'reconcile_deploy'), \
                 patch.object(refresh.subprocess, 'check_output', return_value=''), \
                 patch.object(refresh.publisher.publication, 'gh', return_value='[]'), \
                 patch.object(refresh, 'checkpoints', return_value=[]), \
                 patch.object(refresh, 'amazon_intake', side_effect=intake), \
                 patch.object(refresh, 'write_if_changed'), \
                 patch.object(refresh, 'market_refresh', side_effect=market_boom), \
                 patch.object(refresh, 'follow_main'), \
                 patch.object(refresh, 'save_checkpoint', calls.save), \
                 patch.object(refresh, 'health_report'), \
                 patch.object(refresh.estado, 'guardar', calls.guardar), \
                 patch.object(refresh, 'open_issue', calls.issue), \
                 patch.object(refresh, 'assemble', calls.assemble):
                refresh.refresh(publish=True)
            self.assertEqual(calls.issue.call_args.args[0], 'Carga degradada: precios y portadas (TimeoutError)')
            self.assertEqual(catalogue.read_text(), '["alta"]\n')
            self.assertEqual(market.read_text(), '{"precios": 0}\n')
            self.assertTrue((root / 'assets/reading-covers/alta.webp').exists())
            self.assertTrue((root / 'assets/reading-covers/vieja.webp').exists())
            self.assertFalse((root / 'assets/reading-covers/precio.webp').exists())
            calls.save.assert_called_once()
            calls.guardar.assert_called_once()
            self.assertEqual(calls.assemble.call_args.args[0]['new_books'], ['alta'])
            self.assertFalse(calls.assemble.call_args.kwargs['changed'])

    def test_discard_reverts_tracked_and_removes_new_files_only_in_intake_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            git = lambda *a: subprocess.run(['git', *a], cwd=root, check=True, capture_output=True)
            git('init', '-q'); git('config', 'user.email', 't@t'); git('config', 'user.name', 't')
            (root / 'data').mkdir(); (root / 'assets/reading-covers').mkdir(parents=True)
            (root / 'data/reading-catalogue.json').write_text('{"libros": []}\n')
            (root / 'otro.txt').write_text('x')
            git('add', '.'); git('commit', '-qm', 'base')
            (root / 'data/reading-catalogue.json').write_text('{"libros": [1]}\n')
            (root / 'assets/reading-covers/isbn-1.webp').write_bytes(b'img')
            (root / 'nuevo-fuera.txt').write_text('se queda')
            refresh.discard_intake_writes(root)
            self.assertEqual(json.loads((root / 'data/reading-catalogue.json').read_text()), {'libros': []})
            self.assertFalse((root / 'assets/reading-covers/isbn-1.webp').exists())
            self.assertTrue((root / 'nuevo-fuera.txt').exists())


if __name__ == '__main__':
    unittest.main()
