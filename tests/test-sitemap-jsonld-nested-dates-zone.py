from __future__ import annotations
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('zone_sitemap_jsonld_nested', ROOT / 'scripts/build-sitemap.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def extract(payload):
    html = '<script type="application/ld+json">' + json.dumps(payload) + '</script>'
    return module.extract_date_modified(html)

cases = [
    ({'@graph': [{'@type': 'Article', 'dateModified': '2026-10-24'}]}, '2026-10-24'),
    ([{'@type': 'WebSite'}, {'@type': 'Article', 'dateModified': '2026-10-23'}], '2026-10-23'),
    ([{'@graph': [{'@type': 'Article', 'dateModified': '2026-10-22'}]}], '2026-10-22'),
    ({'@graph': [{'@type': 'WebPage', 'dateModified': '2026-10-21'}]}, '2026-10-21'),
]
for payload, expected in cases:
    result = extract(payload)
    assert result == expected, f'Fecha JSON-LD no localizada: {payload} -> {result}'
print('PASS sitemap JSON-LD nested dates')
