from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

feed = load('feed_parity', 'build-feed.py')
pagefind = load('pagefind_parity', 'build-pagefind-index.py')
fixtures = [
    '<meta name="robots" content="noindex">',
    '<meta content="noindex" name="robots">',
    "<META NAME='ROBOTS' CONTENT='NOINDEX, FOLLOW'>",
    '<meta name="robots" content="index,follow">',
    '<meta name="description" content="noindex">',
    '<meta name="robots" content="index"><meta name="robots" content="noindex">',
    '<meta name="robots" content="follow">',
]
for fixture in fixtures:
    actual = feed.is_noindex(fixture)
    expected = pagefind.is_noindex(fixture)
    assert actual == expected, f'Decisión RSS/Pagefind diferente: {fixture}: {actual}/{expected}'
print('Cross-builder robots parity: OK')