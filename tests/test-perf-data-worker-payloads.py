#!/usr/bin/env python3
from pathlib import Path
import gzip

ROOT = Path(__file__).resolve().parents[1]
files = list((ROOT / 'data').rglob('*.json'))
files += list((ROOT / 'convocatorias-escritores').rglob('*.json'))
files += list(ROOT.glob('cloudflare-worker-*.js'))
limits = {'.json': 192 * 1024, '.js': 128 * 1024}
failures = []
results = []

for path in sorted(set(files)):
    if not path.is_file():
        continue
    raw = path.read_bytes().replace(b'\r\n', b'\n')
    compressed = gzip.compress(raw, compresslevel=9, mtime=0)
    limit = limits[path.suffix.lower()]
    rel = path.relative_to(ROOT).as_posix()
    results.append((rel, len(raw), len(compressed)))
    if len(compressed) > limit:
        failures.append(f'{rel}: gzip={len(compressed)} > {limit} B; raw={len(raw)} B')

assert results, 'No se encontraron payloads'
for rel, raw, compressed in sorted(results, key=lambda row: row[2], reverse=True)[:15]:
    print(f'{rel}: raw={raw} gzip={compressed}')
assert not failures, '\n'.join(failures)
print(f'PASS {len(results)} payloads JSON/Worker')
