from pathlib import Path
import fnmatch
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]

class CrossEngineWorkflowCoverage(unittest.TestCase):
    def test_all_cross_engine_tests_trigger_workflow(self):
        workflow = (ROOT / '.github/workflows/cross-engine-smoke.yml').read_text(encoding='utf-8')
        paths_block = re.search(r'(?m)^    paths:\s*\n((?:      - .*\n)+)', workflow)
        self.assertIsNotNone(paths_block, 'No existe filtro paths en pull_request')
        patterns = re.findall(r"(?m)^      - ['\"]?([^'\"\n]+)", paths_block.group(1))
        files = sorted((ROOT / 'qa').glob('*cross-engine*.mjs'))
        self.assertTrue(files, 'No se encontraron pruebas multinavegador')
        missing = []
        for file in files:
            relative = file.relative_to(ROOT).as_posix()
            if not any(fnmatch.fnmatchcase(relative, pattern) for pattern in patterns):
                missing.append(relative)
        self.assertEqual(missing, [], f'Pruebas sin activación automática: {missing}')

if __name__ == '__main__':
    unittest.main()
