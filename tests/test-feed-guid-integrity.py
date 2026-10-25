#!/usr/bin/env python3
"""Integridad de GUID y URL del feed generado."""
import importlib.util
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feed_guid_qa', ROOT / 'scripts/build-feed.py')
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)

class FeedGuidIntegrity(unittest.TestCase):
    def test_committed_feed_identity(self):
        path = ROOT / 'cuaderno/feed.xml'
        self.assertTrue(path.is_file())
        root = ET.fromstring(path.read_bytes())
        items = root.findall('./channel/item')
        self.assertGreaterEqual(len(items), 5)
        seen = set()
        for item in items:
            link = item.findtext('link')
            guid = item.findtext('guid')
            title = item.findtext('title')
            with self.subTest(link=link):
                self.assertTrue(title and title.strip())
                self.assertEqual(guid, link)
                parsed = urlparse(link or '')
                self.assertEqual(parsed.scheme, 'https')
                self.assertEqual(parsed.hostname, 'davidportodiaz.com')
                self.assertFalse(parsed.fragment)
                self.assertNotIn(guid, seen)
                seen.add(guid)

    def test_builder_output_has_same_identity_rules(self):
        items, _ = feed.collect_items()
        generated = ET.fromstring(feed.build_feed_bytes(items))
        entries = generated.findall('./channel/item')
        self.assertTrue(entries)
        self.assertEqual(len({e.findtext('guid') for e in entries}), len(entries))
        for entry in entries:
            self.assertEqual(entry.findtext('guid'), entry.findtext('link'))

if __name__ == '__main__':
    unittest.main()
