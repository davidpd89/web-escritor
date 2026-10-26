from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]

class CrossEngineNetworkIsolation(unittest.TestCase):
    def test_smoke_blocks_external_network(self):
        source = (ROOT / 'qa/cross-engine-smoke.mjs').read_text(encoding='utf-8')
        self.assertIn('async function blockExternalNetwork(page)', source)
        block = source.split('async function blockExternalNetwork(page)', 1)[1]
        block = block.split('\nasync function ', 1)[0]
        self.assertIn('route.abort()', block)
        self.assertIn('route.continue()', block)
        self.assertRegex(block, r'https\?')
        self.assertRegex(source, r'await\s+blockExternalNetwork\(page\)')
        main = source.split('async function main()', 1)[1]
        main = main.split('\nmain().catch(', 1)[0]
        self.assertRegex(
            main,
            r'const page\s*=\s*await context\.newPage\(\);\s*'
            r'await blockExternalNetwork\(page\);\s*'
            r'const errors\s*=\s*await checkRoute\(page,\s*engineName,\s*routePath\);',
            'La interceptación debe completarse antes de comprobar y navegar por la ruta'
        )
        check_route = source.split('async function checkRoute(', 1)[1]
        check_route = check_route.split('\nasync function main()', 1)[0]
        self.assertRegex(
            check_route,
            r'await\s+page\.goto\(',
            'La función de comprobación debe realizar una navegación esperada'
        )

if __name__ == '__main__':
    unittest.main()
