import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAFE = {'no-referrer', 'same-origin', 'strict-origin', 'strict-origin-when-cross-origin'}


class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.policies = []

    def handle_starttag(self, tag, attrs):
        if tag != 'meta':
            return
        a = dict(attrs)
        if a.get('name', '').lower() == 'referrer':
            self.policies.append(a.get('content', '').strip().lower())


class TestReferrerPrivacy(unittest.TestCase):
    def test_referrer_does_not_expose_full_path(self):
        for page in ('eventos.html', 'ferias.html'):
            with self.subTest(page=page):
                parser = Document()
                parser.feed((ROOT / page).read_text(encoding='utf-8'))
                self.assertEqual(len(parser.policies), 1, f'{page}: política referrer ausente o duplicada: {parser.policies}')
                self.assertIn(parser.policies[0], SAFE, f'{page}: política referrer potencialmente filtradora: {parser.policies[0]}')


if __name__ == '__main__':
    unittest.main()