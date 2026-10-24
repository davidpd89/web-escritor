import json
import re
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FACTS = json.loads((ROOT / 'editorial-facts.json').read_text(encoding='utf-8'))['books']['lasManecillasDelRecuerdo']
BOOK = (ROOT / 'las-manecillas-del-recuerdo/index.html').read_text(encoding='utf-8')
KINDLE = (ROOT / 'las-manecillas-del-recuerdo/kindle/index.html').read_text(encoding='utf-8')


def published(source, fmt):
    visible = re.search(r'<time class="book-date" datetime="(\d{4}-\d{2}-\d{2})"', source)
    assert visible, 'Falta fecha visible'
    scripts = re.findall(r'<script type="application/ld\+json">(.*?)</script>', source, re.S)
    nodes = [node for script in scripts for node in json.loads(script).get('@graph', [])]
    edition = next(node for node in nodes if node.get('@type') == 'Book' and node.get('bookFormat') == fmt)
    assert edition['datePublished'] == visible.group(1), 'HTML y Book divergen'
    return date.fromisoformat(visible.group(1))


def verify(book, kindle):
    physical = published(book, 'https://schema.org/Paperback')
    digital = published(kindle, 'https://schema.org/EBook')
    assert physical == date.fromisoformat(FACTS['publicationDate'])
    assert digital == date.fromisoformat(FACTS['kindleEdition']['publicationDate'])
    assert digital < physical


class TemporalRelations(unittest.TestCase):
    def test_actual_contract(self):
        verify(BOOK, KINDLE)

    def test_swapped_visible_dates_are_detected(self):
        altered = KINDLE.replace('datetime="2026-08-12"', 'datetime="2026-09-03"', 1)
        with self.assertRaises(AssertionError):
            verify(BOOK, altered)

    def test_swapped_structured_dates_are_detected(self):
        altered = KINDLE.replace('"datePublished": "2026-08-12"', '"datePublished": "2026-09-03"', 1)
        with self.assertRaises(AssertionError):
            verify(BOOK, altered)


if __name__ == '__main__':
    unittest.main()
