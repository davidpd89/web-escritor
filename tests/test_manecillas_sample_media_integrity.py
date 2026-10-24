import html
import re
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'assets/downloads/manecillas/las-manecillas-del-recuerdo-muestra-capitulo-1-1'
PAGE = ROOT / 'las-manecillas-del-recuerdo/fragmentos/index.html'


def normalise(value):
    value = re.sub(r'<[^>]*>', ' ', value)
    return re.sub(r'\s+', ' ', html.unescape(value)).strip()


class SampleIntegrity(unittest.TestCase):
    def test_three_representations(self):
        source = PAGE.read_text(encoding='utf-8')
        match = re.search(r'<section[^>]+id="fragmento-1"[\s\S]*?<div class="excerpt-field" data-nosnippet>([\s\S]*?)</div>', source)
        self.assertIsNotNone(match)
        paragraphs = re.findall(r'<p>(.*?)</p>', match.group(1), re.S)
        self.assertGreaterEqual(len(paragraphs), 3)
        txt = normalise(BASE.with_suffix('.txt').read_text(encoding='utf-8-sig'))
        with zipfile.ZipFile(BASE.with_suffix('.epub')) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(archive.read('mimetype').decode().strip(), 'application/epub+zip')
            names = [name for name in archive.namelist() if name.lower().endswith(('.xhtml', '.html', '.htm'))]
            self.assertTrue(names)
            epub = normalise(' '.join(archive.read(name).decode('utf-8-sig') for name in names))
        for paragraph in paragraphs[:3]:
            expected = normalise(paragraph)
            self.assertGreater(len(expected), 30)
            self.assertIn(expected, txt, 'Divergencia en TXT')
            self.assertIn(expected, epub, 'Divergencia en EPUB')


if __name__ == '__main__':
    unittest.main()
