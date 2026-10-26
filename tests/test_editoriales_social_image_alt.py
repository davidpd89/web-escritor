import html as html_lib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def get_meta(document, attribute, key):
    pattern = rf'<meta\s+{attribute}="{re.escape(key)}"\s+content="([^"]*)"'
    match = re.search(pattern, document, re.I)
    return html_lib.unescape(match.group(1)) if match else None


class EditorialSocialAlt(unittest.TestCase):
    def test_accessible_social_descriptions(self):
        pages = sorted((ROOT / 'editoriales').rglob('index.html'))
        self.assertTrue(pages, 'editoriales: no hay páginas que revisar')
        for page in pages:
            source = page.read_text(encoding='utf-8')
            og = get_meta(source, 'property', 'og:image')
            tw = get_meta(source, 'name', 'twitter:image')
            og_alt = get_meta(source, 'property', 'og:image:alt')
            tw_alt = get_meta(source, 'name', 'twitter:image:alt')
            self.assertTrue(og and tw, f'{page}: faltan imágenes sociales')
            for label, value in [('og:image:alt', og_alt), ('twitter:image:alt', tw_alt)]:
                self.assertIsNotNone(value, f'{page}: falta {label}')
                self.assertGreaterEqual(len(value.strip().split()), 3, f'{page}: {label} insuficiente: {value!r}')
                self.assertNotRegex(value.strip(), r'(?i)^(https?://|[^ ]+\.(jpg|jpeg|png|webp)$)', f'{page}: {label} no describe la imagen')
            if og == tw:
                self.assertEqual(og_alt, tw_alt, f'{page}: la misma imagen tiene descripciones sociales contradictorias')


if __name__ == '__main__':
    unittest.main()