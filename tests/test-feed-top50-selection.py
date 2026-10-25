#!/usr/bin/env python3
"""Selección de las 50 entradas más recientes."""
import importlib.util
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feed_top50_qa', ROOT / 'scripts/build-feed.py')
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)

class Top50Selection(unittest.TestCase):
    def test_only_latest_fifty(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for i in range(65):
                day = (date(2026, 1, 1) + timedelta(days=i)).isoformat()
                path = Path(tmp) / f'{i:03d}.html'
                path.write_text(f'<title>Artículo {i}</title><link rel="canonical" href="https://davidportodiaz.com/cuaderno/item-{i}/"><meta name="datePublished" content="{day}">', encoding='utf-8')
                paths.append(str(path))
            with patch.object(feed, 'find_html_files', return_value=iter(reversed(paths))):
                items, skipped = feed.collect_items()
            self.assertEqual(len(items), 50)
            self.assertEqual(skipped, 0)
            self.assertEqual([Path(x['path']).stem for x in items], [f'{i:03d}' for i in range(64, 14, -1)])

if __name__ == '__main__':
    unittest.main()
