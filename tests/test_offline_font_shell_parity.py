import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class TestOfflineFontParity(unittest.TestCase):
    def test_font_dependencies(self):
        html = (ROOT / 'offline.html').read_text(encoding='utf-8')
        sw = (ROOT / 'service-worker.js').read_text(encoding='utf-8')
        shell = re.search(r'const APP_SHELL\s*=\s*\[([\s\S]*?)\];', sw)
        self.assertIsNotNone(shell)
        entries = set(re.findall(r'[\x22\x27](/[^\x22\x27]+)[\x22\x27]', shell.group(1)))
        fonts = set(re.findall(r'url\([\x22\x27]?(/assets/fonts/[^)\x22\x27]+)', html))
        self.assertTrue(fonts)
        for font in fonts:
            with self.subTest(font=font):
                self.assertIn(font, entries)
                self.assertTrue((ROOT / font.lstrip('/')).is_file())

if __name__ == '__main__':
    unittest.main()