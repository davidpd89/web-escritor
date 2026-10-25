from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('zone_sitemap_calendar', ROOT / 'scripts/build-sitemap.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

invalid = [
    '2026-02-29',
    '2026-04-31',
    '2026-13-01',
    '2026-00-10',
    '2026-01-00',
    '2026-12-32',
    '2025-02-29',
]
for value in invalid:
    result = module.normalize_lastmod(value)
    assert result is None, f'Fecha imposible aceptada: {value} -> {result}'

valid = {
    '2024-02-29': '2024-02-29',
    '2026-02-28': '2026-02-28',
    '2026-12-31': '2026-12-31',
    '2026-01-01': '2026-01-01',
}
for value, expected in valid.items():
    assert module.normalize_lastmod(value) == expected

xml = module.render_xml({'https://davidportodiaz.com/': None})
assert '<lastmod>' not in xml
print('PASS sitemap lastmod calendar validation')
