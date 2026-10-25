#!/usr/bin/env python3
"""Roundtrip XML para contenido editorial del RSS."""
import importlib.util
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feed_xml_qa', ROOT / 'scripts/build-feed.py')
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)

class FeedXmlRoundtrip(unittest.TestCase):
    def test_special_characters_preserved(self):
        title = 'Fantasía & misterio: «A < B»'
        description = 'Una lectura con <script>alert(1)</script>, comillas y símbolos &.'
        item = {
            'title': title,
            'description': description,
            'url': 'https://davidportodiaz.com/cuaderno/prueba/',
            'date': '2026-10-25',
        }
        payload = feed.build_feed_bytes([item])
        root = ET.fromstring(payload)
        entry = root.find('./channel/item')
        self.assertIsNotNone(entry)
        self.assertEqual(entry.findtext('title'), title)
        self.assertEqual(entry.findtext('description'), description)
        self.assertEqual(entry.findtext('link'), item['url'])
        self.assertEqual(entry.findtext('guid'), item['url'])
        self.assertIsNone(entry.find('./description/script'))
        self.assertEqual(len(root.findall('./channel/item')), 1)

    def test_empty_feed_is_valid_xml(self):
        root = ET.fromstring(feed.build_feed_bytes([]))
        self.assertEqual(root.tag, 'rss')
        self.assertEqual(root.attrib.get('version'), '2.0')
        self.assertEqual(root.findall('./channel/item'), [])

if __name__ == '__main__':
    unittest.main()
