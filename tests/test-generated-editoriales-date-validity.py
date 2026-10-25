from __future__ import annotations
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
records = json.loads((ROOT / 'data/editoriales.json').read_text(encoding='utf-8'))['publishers']
reference = date(2026, 10, 25)

for record in records:
    if record.get('publish') is not True:
        continue
    slug = record['slug']
    raw = record.get('verified_at')
    assert isinstance(raw, str) and raw, f'{slug}: sin verified_at'
    verified = date.fromisoformat(raw)
    assert verified.isoformat() == raw, f'{slug}: fecha no normalizada'
    assert verified <= reference, f'{slug}: fecha futura {raw}'
print('Editoriales date validity: OK')