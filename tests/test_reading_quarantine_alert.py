"""La alerta de cuarentena no borra las cifras del lote recuperado ni comenta dos veces lo mismo (#1344)."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('refresh_alert', ROOT / 'scripts/refresh-reading-catalogue.py')
refresh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refresh)


class QuarantineAlertTest(unittest.TestCase):
    def test_conserva_stats_del_lote_recuperado(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / '.ci/reading-intake/publisher-report.json'
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({'recuperado_de': 'x', 'new_books': [], 'stats': {'accepted': 7}}), encoding='utf-8')
            with mock.patch.object(refresh, 'ROOT', root), mock.patch.dict(refresh.reading_quarantine.LAST, {'alert': True}),                     mock.patch.dict('os.environ', {'GITHUB_ACTIONS': '', 'GITHUB_STEP_SUMMARY': ''}):
                refresh.quarantine_alert({'new_books': [], 'updated_books': [], 'stats': {}}, [])
            saved = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(saved['stats'], {'accepted': 7}, 'la cadena nocturna lee stats.accepted')
        self.assertEqual(saved['recuperado_de'], 'x')
        self.assertTrue(saved['quarantine_rate_alert'])

    def test_reintento_no_comenta_dos_veces(self):
        calls = []

        def run(args, **_):
            calls.append(args[1:])
            out = ''
            if args[1:3] == ['issue', 'list']:
                out = json.dumps([{'number': 5, 'title': 'Cuarentena: "x"'}])
            elif args[1:3] == ['issue', 'view']:
                out = json.dumps({'body': 'otro', 'comments': [{'body': 'mismo'}]})
            return subprocess.CompletedProcess(args, 0, out, '')
        with mock.patch.object(refresh.subprocess, 'run', run):
            refresh.open_issue('Cuarentena: "x"', 'mismo')
            refresh.open_issue('Cuarentena: "x"', 'nuevo')
        busqueda = next(c for c in calls if c[:2] == ['issue', 'list'])
        self.assertNotIn('"x"', busqueda[busqueda.index('--search') + 1].strip('"'), 'comillas de la causa fuera de la búsqueda')
        self.assertIn('--limit', busqueda)
        self.assertEqual([c for c in calls if c[:2] == ['issue', 'comment']], [['issue', 'comment', '5', '--body', 'nuevo']])


if __name__ == '__main__':
    unittest.main()
