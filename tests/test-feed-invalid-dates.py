#!/usr/bin/env python3
"""Fechas inválidas y resistencia del serializador RSS."""
import importlib.util
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feed_invalid_dates_qa', ROOT / 'scripts/build-feed.py')
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)

class InvalidDates(unittest.TestCase):
    def test_invalid_dates_return_none(self):
        for value in ('2026-02-30', '2026-13-01', '2026-00-01', '2026-10', 'no-es-fecha', ''):
            with self.subTest(value=value):
                self.assertIsNone(feed.iso_to_rfc2822(value))

    def test_invalid_date_does_not_break_other_items(self):
        items = [
            {'title': 'Primero', 'url': 'https://davidportodiaz.com/cuaderno/a/', 'date': '2026-02-30'},
            {'title': 'Segundo', 'url': 'https://davidportodiaz.com/cuaderno/b/', 'date': '2026-10-20'},
        ]
        xml = ET.fromstring(feed.build_feed_bytes(items))
        records = xml.findall('./channel/item')
        self.assertEqual(len(records), 2)
        self.assertIsNone(records[0].find('pubDate'))
        self.assertIsNotNone(records[1].find('pubDate'))

if __name__ == '__main__':
    unittest.main()
