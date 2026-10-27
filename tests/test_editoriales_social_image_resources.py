import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
HOST = 'davidportodiaz.com'


def pages():
    return sorted((ROOT / 'editoriales').rglob('index.html'))


def meta(html, key, attribute):
    pattern = rf'<meta\s+{attribute}="{re.escape(key)}"\s+content="([^"]+)"'
    match = re.search(pattern, html, re.I)
    return match.group(1) if match else None


class EditorialSocialResources(unittest.TestCase):
    def test_local_social_images_exist(self):
        documents = pages()
        self.assertTrue(documents, 'editoriales: no se encontraron documentos publicados')
        for page in documents:
            html = page.read_text(encoding='utf-8')
            for key, attr in [('og:image', 'property'), ('twitter:image', 'name')]:
                with self.subTest(page=str(page.relative_to(ROOT)), field=key):
                    value = meta(html, key, attr)
                    self.assertTrue(value, f'{page}: falta {key}')
                    url = urlsplit(value)
                    self.assertEqual(url.scheme, 'https', f'{page}: {key} usa {value}')
                    self.assertEqual(url.netloc, HOST, f'{page}: {key} apunta a {value}')
                    self.assertFalse(url.query or url.fragment, f'{page}: URL multimedia no canónica: {value}')
                    target = (ROOT / unquote(url.path).lstrip('/')).resolve()
                    self.assertTrue(target.is_relative_to(ROOT), f'{page}: recurso fuera del repositorio: {value}')
                    self.assertTrue(target.is_file(), f'{page}: imagen inexistente: {value}')
                    self.assertGreater(target.stat().st_size, 0, f'{page}: imagen vacía: {value}')


if __name__ == '__main__':
    unittest.main()