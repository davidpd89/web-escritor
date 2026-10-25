#!/usr/bin/env python3
"""Determinismo del feed ante distintos órdenes de descubrimiento."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feed_order_qa', ROOT / 'scripts/build-feed.py')
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)

class FilesystemOrderDeterminism(unittest.TestCase):
    def test_reversed_discovery_same_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for slug, date in [('a', '2026-10-20'), ('b', '2026-10-21'), ('c', '2026-10-20')]:
                path = Path(tmp) / (slug + '.html')
                path.write_text('<title>' + slug + '</title><link rel="canonical" href="https://davidportodiaz.com/cuaderno/' + slug + '/"><meta name="datePublished" content="' + date + '">', encoding='utf-8')
                paths.append(str(path))
            outputs = []
            for ordering in (paths, list(reversed(paths)), [paths[1], paths[2], paths[0]]):
                with patch.object(feed, 'find_html_files', return_value=iter(ordering)):
                    items, skipped = feed.collect_items()
                    self.assertEqual(skipped, 0)
                    outputs.append(feed.build_feed_bytes(items))
            self.assertEqual(outputs[0], outputs[1])
            self.assertEqual(outputs[1], outputs[2])

if __name__ == '__main__':
    unittest.main()
