"""La fuente decorativa del catálogo es un subconjunto que cubre todas las etiquetas que pinta."""
import json
import re
import unittest
from pathlib import Path

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / 'assets/reading-catalogue.css').read_text(encoding='utf-8')
JS = (ROOT / 'assets/reading-catalogue.js').read_text(encoding='utf-8')
BUILDER = (ROOT / 'scripts/build-reading-catalogue.py').read_text(encoding='utf-8')


class CatalogueFontSubsetTest(unittest.TestCase):
    def test_subset_covers_every_novelty_label(self):
        src = re.search(r"font-family:CatalogueNovelty;src:url\('([^']+)'\)", CSS).group(1)
        self.assertIn('subset', src)
        font = ROOT / src.lstrip('/')
        self.assertLess(font.stat().st_size, 4096)
        line = re.search(r"const text = fresh \? (.+);", JS).group(1)
        labels = {json.loads('"' + l + '"') for l in re.findall(r"'([^']+)'", line)}
        labels |= set(re.findall(r'hidden>([^<]+)</span>', BUILDER))
        self.assertTrue({'Novedad', 'Próximamente'} <= labels, labels)
        cmap = TTFont(font).getBestCmap()
        missing = {c for l in labels for c in l if ord(c) not in cmap}
        self.assertFalse(missing, f'Glifos sin cubrir en el subconjunto: {missing}')


if __name__ == '__main__':
    unittest.main()
