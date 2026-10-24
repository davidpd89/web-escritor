import html
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'las-manecillas-del-recuerdo/fragmentos/index.html').read_text(encoding='utf-8')


def plain(value):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]*>', ' ', value))).strip()


class ExcerptSnippets(unittest.TestCase):
    def test_no_literary_openings_in_social_descriptions(self):
        sections = re.findall(r'<div class="excerpt-field" data-nosnippet>(.*?)</div>', SOURCE, re.S)
        self.assertEqual(len(sections), 3)
        metadata = re.findall(r'<meta\s+[^>]*(?:name|property)="(?:description|og:description|twitter:description)"[^>]*>', SOURCE)
        self.assertEqual(len(metadata), 3)
        descriptions = ' '.join(plain(value) for value in metadata).casefold()
        for section in sections:
            first = re.search(r'<p>(.*?)</p>', section, re.S)
            self.assertIsNotNone(first)
            opening = plain(first.group(1))
            self.assertGreater(len(opening), 35)
            self.assertNotIn(opening[:50].casefold(), descriptions)

    def test_every_excerpt_remains_excluded_from_snippets(self):
        fields = re.findall(r'<div\s+class="excerpt-field"([^>]*)>', SOURCE)
        self.assertEqual(len(fields), 3)
        self.assertTrue(all(re.search(r'\bdata-nosnippet\b', attrs) for attrs in fields))


if __name__ == '__main__':
    unittest.main()
