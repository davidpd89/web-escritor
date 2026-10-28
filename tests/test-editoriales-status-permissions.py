from __future__ import annotations
import copy
import importlib.util
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('builder', ROOT / 'scripts' / 'build-editoriales.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
data = json.loads((ROOT / 'data/editoriales.json').read_text(encoding='utf-8'))['publishers']
base = copy.deepcopy(next(r for r in data if r['status'] == 'open' and r.get('submission_email')))
today = date(2026, 10, 23)
builder.validate_record(copy.deepcopy(base), set(), today)

cases = [
    ('closed', True, None),
    ('indirect', True, None),
    ('unknown', True, None),
    ('award_only', True, None),
    ('indirect', False, base['submission_email']),
    ('unknown', False, base['submission_email']),
    ('award_only', False, base['submission_email']),
]

for status, direct, email in cases:
    record = copy.deepcopy(base)
    record['status'] = status
    record['direct_submission'] = direct
    record['submission_email'] = email
    try:
        builder.validate_record(record, set(), today)
    except builder.ValidationError:
        pass
    else:
        raise AssertionError(f'{status}: publicación contradictoria aceptada; direct={direct}, email={email!r}')

print('PASS editorial status permissions')