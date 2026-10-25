from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('rss_builder', ROOT / 'scripts/build-feed.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

excluded = [
    '<meta name="robots" content="noindex,follow">',
    '<meta content="noindex,follow" name="robots">',
    "<META CONTENT='NOINDEX' NAME='ROBOTS'>",
    '<meta name=robots content=noindex>',
    '<meta name="robots" content="index,follow"><meta content="noindex" name="robots">',
]
allowed = [
    '<meta name="robots" content="index,follow">',
    '<meta name="description" content="noindex">',
    '<script>const message = "noindex";</script>',
]
for html in excluded:
    assert mod.is_noindex(html), f'RSS no excluye: {html}'
for html in allowed:
    assert not mod.is_noindex(html), f'RSS excluye incorrectamente: {html}'
print('RSS robots variants: OK')