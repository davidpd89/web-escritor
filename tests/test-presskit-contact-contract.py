import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('press_builder', ROOT / 'scripts/build-press-kit.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
load = lambda p: json.loads((ROOT / p).read_text(encoding='utf-8'))

class PressContactContract(unittest.TestCase):
    def test_official_contact_page_is_sufficient(self):
        author = load('press-kit/david-porto-diaz.json')
        book = load('press-kit/las-manecillas-del-recuerdo.json')
        editorial = load('editorial-facts.json')
        manifest = {'assets': [], 'documents': []}
        self.assertNotIn('email', author['contact'])
        self.assertTrue(author['contact']['contactPage'].startswith('https://'))
        errors = builder.validate(manifest, book, author, editorial)
        self.assertFalse(any('contacto' in e.lower() or 'email' in e.lower() for e in errors), errors)

    def test_readme_contains_working_contact(self):
        author = load('press-kit/david-porto-diaz.json')
        book = load('press-kit/las-manecillas-del-recuerdo.json')
        readme = builder.make_readme(book, author, {'assets': []}).decode('utf-8')
        self.assertIn(author['contact']['contactPage'], readme)
        self.assertIn('https://davidportodiaz.com/prensa.html', readme)
        self.assertNotIn('Contacto de prensa: \n', readme)
        self.assertNotIn('Página de prensa: \n', readme)

if __name__ == '__main__':
    unittest.main()