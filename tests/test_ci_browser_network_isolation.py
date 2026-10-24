import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ('manecillas-buy-cta-contract.mjs', 'manecillas-funnel-browser.mjs')


class BrowserNetworkIsolation(unittest.TestCase):
    def test_no_real_external_analytics(self):
        for filename in FILES:
            source = (ROOT / 'qa' / filename).read_text(encoding='utf-8')
            with self.subTest(filename=filename):
                self.assertIn('page.route(', source)
                self.assertIn('gc\\.zgo\\.at', source)
                self.assertIn('metricool\\.com', source)
                self.assertIn('route.abort()', source)
                self.assertIn('page.addInitScript(', source)
                self.assertIn('window.goatcounter', source)

    def test_purchase_links_never_reach_remote_servers(self):
        source = (ROOT / 'qa/manecillas-buy-cta-contract.mjs').read_text(encoding='utf-8')
        self.assertIn('amzn\\.to|amazon\\.es', source)
        self.assertIn('route.abort()', source)


if __name__ == '__main__':
    unittest.main()