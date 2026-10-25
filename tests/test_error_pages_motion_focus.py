import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class TestErrorAccessibility(unittest.TestCase):
    def test_offline_motion_and_focus(self):
        src = (ROOT / 'offline.html').read_text(encoding='utf-8')
        self.assertIn('prefers-reduced-motion: reduce', src)
        self.assertIn(':focus-visible', src)
        self.assertIn('outline:', src)
        self.assertIn('viewport-fit=cover', src)
    def test_404_skip_link(self):
        src = (ROOT / '404.html').read_text(encoding='utf-8')
        self.assertIn('href="#contenido"', src)
        self.assertIn('id="contenido"', src)
        self.assertIn('tabindex="-1"', src)
        self.assertIn('class="skip-link"', src)

if __name__ == '__main__':
    unittest.main()