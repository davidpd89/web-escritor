import html
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FACTS = json.loads((ROOT / 'editorial-facts.json').read_text(encoding='utf-8'))['books']['lasManecillasDelRecuerdo']
BOOK = (ROOT / 'las-manecillas-del-recuerdo/index.html').read_text(encoding='utf-8')
KINDLE = (ROOT / 'las-manecillas-del-recuerdo/kindle/index.html').read_text(encoding='utf-8')


def ledger(source):
    block = re.search(r'<dl class="book-meta-ledger"[^>]*>(.*?)</dl>', source, re.S)
    assert block
    pairs = re.findall(r'<dt>(.*?)</dt>\s*<dd>(.*?)</dd>', block.group(1), re.S)
    return {html.unescape(k.strip()): html.unescape(v.strip()) for k, v in pairs}


def verify(book, kindle):
    physical = ledger(book)
    digital = ledger(kindle)
    assert physical['Páginas'] == str(FACTS['numberOfPages'])
    assert physical['ISBN'] == FACTS['isbn']
    assert physical['PVP'] == f"{FACTS['priceEUR']:.2f}".replace('.', ',') + ' €'
    edition = FACTS['kindleEdition']
    assert digital['ISBN-13'] == edition['isbn13']
    assert digital['ASIN'] == edition['asin']
    assert digital['Precio'] == f"{edition['priceEUR']:.2f}".replace('.', ',') + ' €'
    assert physical['ISBN'] != digital['ISBN-13']
    assert physical['PVP'] != digital['Precio']


class NumericMutations(unittest.TestCase):
    def test_unmodified(self):
        verify(BOOK, KINDLE)

    def test_physical_price_mutation_detected(self):
        with self.assertRaises(AssertionError):
            verify(BOOK.replace('<dd>15,99 €</dd>', '<dd>2,99 €</dd>', 1), KINDLE)

    def test_page_count_mutation_detected(self):
        with self.assertRaises(AssertionError):
            verify(BOOK.replace('<dd>272</dd>', '<dd>227</dd>', 1), KINDLE)

    def test_kindle_isbn_mutation_detected(self):
        with self.assertRaises(AssertionError):
            verify(BOOK, KINDLE.replace('<dd>979-8906781925</dd>', '<dd>979-8-90514-935-1</dd>', 1))

    def test_kindle_asin_mutation_detected(self):
        with self.assertRaises(AssertionError):
            verify(BOOK, KINDLE.replace('<dd>B0HHM71F46</dd>', '<dd>B0HHY9MYLM</dd>', 1))


if __name__ == '__main__':
    unittest.main()
