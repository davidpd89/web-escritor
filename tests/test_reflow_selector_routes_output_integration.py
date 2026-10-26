import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import importlib.util

spec = importlib.util.spec_from_file_location('reflow_selector_output', ROOT / 'scripts' / 'ci-select-reflow.py')
selector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selector)


class ReflowSelectorOutputIntegration(unittest.TestCase):
    def test_public_html_change_exports_selected_routes(self):
        target = 'libros/index.html'
        self.assertTrue((ROOT / target).is_file(), f'No existe la página publicada {target}')
        expected = selector.scope_routes([target], exists=lambda p: (ROOT / p).is_file())
        self.assertEqual(expected, ['/', '/libros/'])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'github-output.txt'
            env = dict(os.environ, EVENT_NAME='pull_request', BASE_SHA='base', HEAD_SHA='head', GITHUB_OUTPUT=str(output))
            with patch.object(selector, 'changed_files', return_value=[target]), patch.dict(os.environ, env, clear=True):
                self.assertEqual(selector.main(), 0)
            values = dict(line.split('=', 1) for line in output.read_text(encoding='utf-8').splitlines() if '=' in line)
            self.assertEqual(values.get('run'), 'true', f'{target}: el selector debe ejecutar la auditoría')
            self.assertIn('routes', values, f'{target}: falta routes en GITHUB_OUTPUT; el workflow recibe una cadena vacía y recorre todo el sitio')
            self.assertEqual(set(values['routes'].split(',')), set(expected), f'{target}: rutas exportadas distintas de las seleccionadas')


if __name__ == '__main__':
    unittest.main()