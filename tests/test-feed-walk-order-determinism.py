#!/usr/bin/env python3
import importlib.util
import json
import random
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('rss_walk_qa', ROOT / 'scripts/build-feed.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as tmp:
    paths = []
    for name, day in [('zeta', '2026-10-20'), ('alfa', '2026-10-20'), ('beta', '2026-10-21'), ('gamma', '2026-10-19')]:
        path = Path(tmp) / (name + '.html')
        node = {'@context': 'https://schema.org', '@type': 'Article', 'headline': name, 'url': 'https://davidportodiaz.com/cuaderno/' + name + '/', 'datePublished': day}
        path.write_text('<html><head><script type="application/ld+json">' + json.dumps(node) + '</script></head></html>', encoding='utf-8')
        paths.append(str(path))
    originals = mod.find_html_files
    outputs = []
    try:
        for seed in range(12):
            shuffled = paths[:]
            random.Random(seed).shuffle(shuffled)
            mod.find_html_files = lambda items=shuffled: iter(items)
            items, skipped = mod.collect_items()
            assert len(items) == 4 and skipped == 0
            outputs.append(mod.build_feed_bytes(items))
    finally:
        mod.find_html_files = originals
    assert len(set(outputs)) == 1, 'RSS cambia con el orden de os.walk'
    assert outputs[0].count(b'<item>') == 4
print('PASS: RSS reproducible ante 12 permutaciones')
