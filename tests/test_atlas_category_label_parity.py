import importlib.util
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('atlas_label_parity', ROOT / 'scripts/build-atlas-literario.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class OptionParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.options = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == 'option':
            self.current = {'value': dict(attrs).get('value', ''), 'text': ''}

    def handle_data(self, data):
        if self.current is not None:
            self.current['text'] += data

    def handle_endtag(self, tag):
        if tag == 'option' and self.current is not None:
            self.options.append(self.current)
            self.current = None


class AtlasCategoryLabelParity(unittest.TestCase):
    def test_real_categories_keep_spanish_labels(self):
        data, categories = MODULE.load(ROOT / 'data/atlas-literario.json')
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'atlas-literario'
            MODULE.build(data, categories, out)
            document = (out / 'index.html').read_text(encoding='utf-8')
            parser = OptionParser()
            parser.feed(document)
            actual = {option['value']: option['text'].strip() for option in parser.options if option['value']}
            self.assertEqual(actual, categories, f'/atlas-literario/: categorías visibles distintas de data/atlas-literario.json: {actual!r}')
            self.assertEqual(len(actual), len(categories), '/atlas-literario/: se han perdido categorías del selector')
            self.assertIn('Bibliotecas extraordinarias', actual.values(), '/atlas-literario/: falta el nombre editorial de bibliotecas')
            self.assertIn('Librerías singulares', actual.values(), '/atlas-literario/: se ha perdido la etiqueta con tilde')


if __name__ == '__main__':
    unittest.main()
