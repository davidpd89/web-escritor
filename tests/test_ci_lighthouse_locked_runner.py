from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ['lighthouse-ci.yml', 'ferias-archive-parity-qa.yml']

class LighthouseDependencyTest(unittest.TestCase):
    def test_lighthouse_is_installed_from_shared_lock(self):
        package = json.loads((ROOT / 'package.json').read_text(encoding='utf-8'))
        lock = json.loads((ROOT / 'package-lock.json').read_text(encoding='utf-8'))
        version = package['devDependencies']['@lhci/cli']
        self.assertEqual(lock['packages']['node_modules/@lhci/cli']['version'], version)
        for workflow in WORKFLOWS:
            with self.subTest(workflow=workflow):
                source = (ROOT / '.github/workflows' / workflow).read_text(encoding='utf-8')
                self.assertIn('npm ci', source, 'Falta instalación mediante lockfile')
                self.assertNotIn('npm install --global @lhci/cli', source, 'Instalación paralela fuera del lockfile')
                self.assertTrue('npx --no-install lhci ' in source or './node_modules/.bin/lhci ' in source, 'Lighthouse no se invoca desde dependencias locales')

if __name__ == '__main__':
    unittest.main()