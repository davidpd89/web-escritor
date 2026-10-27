import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


class TypographicFontEgressBoundary(unittest.TestCase):
    def test_editorial_font_sources_remain_local(self):
        path = ROOT / 'assets/v1-fonts.css'
        css = re.sub(r'/\*.*?\*/', '', path.read_text(encoding='utf-8'), flags=re.S)
        faces = re.findall(r'@font-face\s*\{([^}]*)\}', css, re.S)
        self.assertTrue(faces, f'{path}: no se encontraron fuentes editoriales')
        checked = 0
        for face in faces:
            family = re.search(r'font-family\s*:\s*([^;]+)', face)
            name = family.group(1).strip() if family else '(sin familia)'
            for raw in re.findall(r'url\(\s*[\'\"]?([^\)\'\"]+)', face, re.I):
                checked += 1
                url = raw.strip()
                parsed = urlsplit(url)
                self.assertFalse(parsed.scheme or parsed.netloc or url.startswith('//'), f'{path}: {name} carga fuente externa {url}')
                self.assertFalse(url.startswith('/'), f'{path}: {name} debe usar fuente relativa {url}')
                target = (path.parent / parsed.path).resolve()
                self.assertTrue(target.is_relative_to(ROOT / 'assets'), f'{path}: {name} escapa de assets: {url}')
                self.assertTrue(target.is_file(), f'{path}: {name} referencia fuente inexistente {url}')
        self.assertGreater(checked, 0, f'{path}: no se comprobaron archivos de fuentes')


if __name__ == '__main__':
    unittest.main()
