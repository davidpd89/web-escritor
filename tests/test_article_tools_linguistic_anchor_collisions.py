import importlib.util
import re
import unittest
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('article_tools', ROOT / 'scripts/build-article-tools.py')
article_tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(article_tools)

class LinguisticAnchorCollisions(unittest.TestCase):
    def transform(self, headings):
        html = '<!doctype html><html lang="es"><body><main id="main-content">' + headings + '<div id="article-tools"></div></main></body></html>'
        return article_tools.process(html)[0]

    def assert_unique_and_resolved(self, output):
        headings = re.findall(r'<h[23]\b[^>]*\bid="([^"]+)"', output)
        links = [unescape(value) for value in re.findall(r'<a href="#([^"]+)" class="at-toc-link"', output)]
        self.assertGreaterEqual(len(headings), 2)
        self.assertEqual(len(headings), len(set(headings)), 'IDs de encabezados duplicados')
        self.assertEqual(len(links), len(set(links)), 'Índice ambiguo')
        self.assertEqual(set(links), set(headings), 'Enlaces sin encabezado o encabezados omitidos')

    def test_accents_and_repeated_titles(self):
        output = self.transform('<h2>El año</h2><h2>El año</h2><h3>¿Qué ocurrió después?</h3>')
        self.assert_unique_and_resolved(output)
        self.assertIn('el-ano', output)
        self.assertIn('el-ano-2', output)

    def test_existing_duplicate_ids_are_detected(self):
        output = self.transform('<h2 id="seccion">Primera sección</h2><h2 id="seccion">Segunda sección</h2>')
        self.assert_unique_and_resolved(output)

    def test_generated_ids_do_not_collide_with_existing_ids(self):
        output = self.transform('<h2 id="el-ano">Original</h2><h2>El año</h2><h3>Conclusión</h3>')
        self.assert_unique_and_resolved(output)

if __name__ == '__main__':
    unittest.main()