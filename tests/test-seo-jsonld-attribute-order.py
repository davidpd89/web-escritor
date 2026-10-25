#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_sitemap', ROOT / 'scripts/build-sitemap.py')
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

payload = json.dumps({'@context': 'https://schema.org', '@type': 'WebPage', 'dateModified': '2026-10-22'})
tags = [
    '<script type="application/ld+json">',
    '<script id="structured-data" type="application/ld+json">',
    '<script type="application/ld+json" id="structured-data">',
    '<script TYPE="application/ld+json">',
    '<script type = "application/ld+json">',
    "<script type='application/ld+json'>",
]

for opening in tags:
    html = f'<html><head>{opening}{payload}</script></head><body></body></html>'
    result = module.extract_date_modified(html)
    assert result == '2026-10-22', f'JSON-LD no reconocido: {opening!r} -> {result!r}'

print('PASS JSON-LD attribute order invariance')
