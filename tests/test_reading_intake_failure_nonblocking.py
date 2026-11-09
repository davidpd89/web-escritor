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
    def run_refresh(self, intake):
        config = {'autopublish': True, 'amazon_catalogo': {'enabled': True}}
        calls = MagicMock()
        with patch.object(refresh, 'read_json', return_value=config), \
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
             patch.object(refresh, 'assemble', calls.assemble):
            calls.market.return_value = True
            try:
                refresh.refresh(publish=True)
                error = None
            except RuntimeError as exc:
                error = exc
        return calls, error

    def test_failed_intake_still_refreshes_prices_and_covers_then_fails_visibly(self):
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
        self.assertIsNotNone(error)
        self.assertIsInstance(error.__cause__, KeyError)

    def test_successful_intake_keeps_the_normal_flow(self):
        calls, error = self.run_refresh(lambda config, publish: {'new_books': ['a'], 'updated_books': [], 'stats': {'accepted': 1}})
        self.assertIsNone(error)
        calls.discard.assert_not_called()
        calls.market.assert_called_once()
        calls.guardar.assert_called_once()

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
