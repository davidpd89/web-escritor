import unittest
from html.parser import HTMLParser
from pathlib import Path

PAGE = Path(__file__).resolve().parents[1] / 'eventos.html'

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs))

class TestRequests(unittest.TestCase):
    def test_contextual_requests(self):
        parser = Links()
        parser.feed(PAGE.read_text(encoding='utf-8'))
        links = [a for a in parser.links if 'data-email-subject' in a]
        self.assertGreaterEqual(len(links), 4)
        subjects = [a['data-email-subject'].strip() for a in links]
        self.assertTrue(all(subjects))
        for link in links:
            self.assertEqual(link.get('href'), '/prensa.html#contacto')
            self.assertIn('data-email-reveal', link)
        combined = ' '.join(subjects).lower()
        for concept in ('presentación', 'taller', 'club de lectura'):
            self.assertIn(concept, combined)
        self.assertGreaterEqual(len(set(subjects)), 3)
        self.assertTrue((PAGE.parent / 'prensa.html').exists())

if __name__ == '__main__':
    unittest.main()
