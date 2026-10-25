#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
from datetime import date, datetime
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_sitemap', ROOT / 'scripts/build-sitemap.py')
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

valid = {
    '2024-02-29': '2024-02-29',
    '2026-10-25': '2026-10-25',
    '2026-01-01T00:30:00+02:00': '2025-12-31T22:30:00Z',
    '2026-12-31T23:30:00-02:00': '2027-01-01T01:30:00Z',
}
invalid = ['2025-02-29', '2026-02-30', '2026-04-31', '2026-13-01', '2026-00-01', '2026-01-00', 'not-a-date']

for value, expected in valid.items():
    actual = module.normalize_lastmod(value)
    assert actual == expected, (value, expected, actual)

for value in invalid:
    actual = module.normalize_lastmod(value)
    assert actual is None, f'Fecha imposible aceptada: {value} -> {actual}'

ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
for filename in ('sitemap.xml', 'editoriales-sitemap.xml'):
    tree = ET.parse(ROOT / filename)
    for entry in tree.findall('.//s:url', ns):
        loc = entry.findtext('s:loc', namespaces=ns)
        value = entry.findtext('s:lastmod', namespaces=ns)
        if not value:
            continue
        try:
            if 'T' in value:
                datetime.fromisoformat(value.replace('Z', '+00:00'))
            else:
                date.fromisoformat(value)
        except ValueError as exc:
            raise AssertionError(f'{filename}: {loc}: lastmod inválido {value}') from exc

print('PASS sitemap calendar boundaries')
