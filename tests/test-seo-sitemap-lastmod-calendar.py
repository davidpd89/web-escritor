import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sitemap_dates', ROOT / 'scripts/build-sitemap.py')
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

invalid = [
    '2026-02-30',
    '2025-02-29',
    '2026-13-01',
    '2026-00-10',
    '2026-04-31',
    '2026-10-32',
]
for value in invalid:
    assert mod.normalize_lastmod(value) is None, f'lastmod imposible aceptado: {value}'

valid = {
    '2024-02-29': '2024-02-29',
    '2026-10-23': '2026-10-23',
    '2026-10-23T00:30:00+02:00': '2026-10-22T22:30:00Z',
    '2026-10-23T12:00:00Z': '2026-10-23T12:00:00Z',
}
for value, expected in valid.items():
    assert mod.normalize_lastmod(value) == expected, value

print('PASS sitemap calendar boundaries')
