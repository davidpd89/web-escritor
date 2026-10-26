import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
CSS = [ROOT / 'assets/editoriales.css', ROOT / 'assets/v1-editoriales-detail.css']
EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.avif'}


def css_urls(source):
    clean = re.sub(r'/\*.*?\*/', '', source, flags=re.S)
    return re.findall(r'url\(\s*[\x27\"]?([^\x27\"\)]+)[\x27\"]?\s*\)', clean, re.I)


class EditorialCssMediaDependencies(unittest.TestCase):
    def test_local_raster_media_dependencies(self):
        for css in CSS:
            self.assertTrue(css.is_file(), f'editoriales: falta hoja CSS {css}')
            content = css.read_text(encoding='utf-8')
            for raw in css_urls(content):
                value = raw.strip()
                parsed = urlsplit(value)
                if parsed.path.lower().endswith(tuple(EXTENSIONS)):
                    with self.subTest(css=str(css.relative_to(ROOT)), url=value):
                        self.assertFalse(parsed.scheme or parsed.netloc, f'{css}: imagen CSS externa: {value}')
                        target = (ROOT / unquote(parsed.path).lstrip('/')) if parsed.path.startswith('/') else css.parent / unquote(parsed.path)
                        target = target.resolve()
                        self.assertTrue(target.is_relative_to(ROOT), f'{css}: imagen fuera del repositorio: {value}')
                        self.assertTrue(target.is_file(), f'{css}: imagen CSS inexistente: {value}')
                        self.assertGreater(target.stat().st_size, 0, f'{css}: imagen CSS vacía: {value}')


if __name__ == '__main__':
    unittest.main()