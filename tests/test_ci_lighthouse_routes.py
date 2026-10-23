from pathlib import Path
from urllib.parse import urlsplit
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'lighthouserc.json').read_text(encoding='utf-8'))

class LighthouseRoutesTest(unittest.TestCase):
    def test_every_audited_route_exists(self):
        urls = CONFIG['ci']['collect']['url']
        self.assertGreaterEqual(len(urls), 5)
        for url in urls:
            with self.subTest(url=url):
                parsed = urlsplit(url)
                self.assertEqual(parsed.hostname, 'localhost')
                route = parsed.path
                target = ROOT / route.lstrip('/')
                if route.endswith('/'):
                    target = target / 'index.html'
                self.assertTrue(target.is_file(), f'{url}: falta {target}')
                text = target.read_text(encoding='utf-8')
                self.assertRegex(text, r'(?is)<html\b')
                self.assertRegex(text, r'(?is)<title\b[^>]*>\s*[^<\s]')
                self.assertRegex(text, r'(?is)<h1\b[^>]*>')
                self.assertNotRegex(text, r'(?is)<meta\b[^>]*name=[\'\"]robots[\'\"][^>]*content=[\'\"][^\'\"]*noindex')

if __name__ == '__main__':
    unittest.main()