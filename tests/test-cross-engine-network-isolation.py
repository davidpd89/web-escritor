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
        navigation = source.find('page.goto(')
        installation = source.find('await blockExternalNetwork(page)')
        self.assertGreaterEqual(navigation, 0)
        self.assertGreaterEqual(installation, 0)
        self.assertLess(installation, navigation, 'La interceptación debe instalarse antes de la navegación')

if __name__ == '__main__':
    unittest.main()
