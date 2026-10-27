from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGES = [
    'clubes-de-lectura/preparar-sesion/index.html',
    'clubes-de-lectura/samuel-entre-mundos/index.html',
    'clubes-de-lectura/samuel-entre-mundos/guia-imprimible/index.html',
]

class ActiveAttributes(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.errors = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            name = name.lower()
            value = (value or '').strip()
            if name.startswith('on') and len(name) > 2:
                self.errors.append(f'<{tag}> atributo {name}')
            if name in ('href', 'src', 'action', 'formaction') and value.lower().startswith('javascript:'):
                self.errors.append(f'<{tag}> {name}={value!r}')
            if name == 'srcdoc':
                self.errors.append(f'<{tag}> atributo srcdoc')

    handle_startendtag = handle_starttag

class ClubActiveAttributeTests(unittest.TestCase):
    def test_no_executable_html_attributes(self):
        for relative in PAGES:
            with self.subTest(page=relative):
                source = ROOT / relative
                self.assertTrue(source.is_file(), f'{relative}: documento inexistente')
                parser = ActiveAttributes()
                parser.feed(source.read_text(encoding='utf-8'))
                parser.close()
                self.assertEqual(parser.errors, [], f'{relative}: atributos ejecutables: {parser.errors}')

if __name__ == '__main__':
    unittest.main()
