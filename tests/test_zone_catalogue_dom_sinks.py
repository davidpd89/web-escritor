import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'assets/reading-catalogue.js'


class CatalogueDOMSinks(unittest.TestCase):
    def test_catalogue_uses_safe_dom_destinations(self):
        source = SOURCE.read_text(encoding='utf-8')
        self.assertIn('function renderMarket()', source)
        self.assertIn('function renderFacets(v)', source)
        self.assertIn('function setupQuiz()', source)
        self.assertIn('function renderPagination(pages)', source)
        forbidden = re.compile(r'\b(?:innerHTML|outerHTML)\s*=|\binsertAdjacentHTML\s*\(|\bdocument\.write\s*\(|\b(?:eval|Function)\s*\(')
        for match in forbidden.finditer(source):
            line = source.count('\n', 0, match.start()) + 1
            self.fail(f'{SOURCE.relative_to(ROOT)}:{line}: destino HTML o ejecución dinámica incompatible con datos bibliográficos: {match.group()}')
        self.assertRegex(source, r'link\.append\(ratingLabel\(r\)')
        self.assertIn('element.textContent = label', source)
        self.assertIn('label.querySelector(\'[data-facet-count]\').textContent', source)


if __name__ == '__main__':
    unittest.main()