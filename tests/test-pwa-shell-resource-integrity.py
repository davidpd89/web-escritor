#!/usr/bin/env python3
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class TestPwaShell(unittest.TestCase):
    def test_install_resources_exist(self):
        worker = (ROOT / 'service-worker.js').read_text(encoding='utf-8')
        match = re.search(r'const APP_SHELL\s*=\s*\[([^\]]+)\]', worker, re.S)
        self.assertIsNotNone(match, 'service-worker.js: no se localiza APP_SHELL')
        urls = re.findall(r'[\"\'](/[^\"\']+)[\"\']', match.group(1))
        self.assertTrue(urls, 'service-worker.js: APP_SHELL vacío')
        for url in urls:
            with self.subTest(url=url):
                path = ROOT / url.lstrip('/')
                self.assertTrue(path.is_file(), f'{url}: recurso de instalación ausente')
                self.assertGreater(path.stat().st_size, 0, f'{url}: recurso vacío')

    def test_manifest_icons_are_part_of_shell(self):
        manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
        worker = (ROOT / 'service-worker.js').read_text(encoding='utf-8')
        match = re.search(r'const APP_SHELL\s*=\s*\[([^\]]+)\]', worker, re.S)
        self.assertIsNotNone(match, 'service-worker.js: APP_SHELL ausente')
        shell = set(re.findall(r'[\"\'](/[^\"\']+)[\"\']', match.group(1)))
        for icon in manifest['icons']:
            self.assertIn(icon['src'], shell, f"{icon['src']}: icono instalable fuera del shell offline")
        self.assertIn('/offline.html', shell)
        self.assertIn('/manifest.json', shell)

if __name__ == '__main__': unittest.main()
