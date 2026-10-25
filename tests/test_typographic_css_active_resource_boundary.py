import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
FILES = ('assets/v1-fonts.css', 'assets/v1-tokens.css', 'assets/v1-base.css', 'assets/v1-shell.css')


class TypographicCSSActiveResourceBoundary(unittest.TestCase):
    def test_shared_typography_has_no_active_external_css(self):
        checked = 0
        for name in FILES:
            path = ROOT / name
            css = re.sub(r'/\*.*?\*/', '', path.read_text(encoding='utf-8'), flags=re.S)
            self.assertNotRegex(css, r'(?i)expression\s*\(', f'{name}: expresión CSS ejecutable')
            self.assertNotRegex(css, r'(?i)javascript\s*:', f'{name}: esquema javascript en CSS')
            imports = re.findall(r'@import\s+(?:url\(\s*)?[\'\"]?([^\s\)\'\";]+)', css, re.I)
            for url in imports:
                checked += 1
                parsed = urlsplit(url)
                self.assertFalse(parsed.scheme or parsed.netloc or url.startswith('//'), f'{name}: importación CSS externa {url}')
                target = (ROOT / parsed.path.lstrip('/')).resolve() if url.startswith('/') else (path.parent / parsed.path).resolve()
                self.assertTrue(target.is_relative_to(ROOT), f'{name}: importación fuera del sitio {url}')
                self.assertTrue(target.is_file(), f'{name}: importación CSS inexistente {url}')
        self.assertGreater(checked, 0, 'No se comprobaron importaciones CSS compartidas')


if __name__ == '__main__':
    unittest.main()
