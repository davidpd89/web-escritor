from __future__ import annotations
import copy
import importlib.util
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('editoriales_history_chronology', ROOT / 'scripts/build-editoriales.py')
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
records = json.loads((ROOT / 'data/editoriales.json').read_text(encoding='utf-8'))['publishers']
record = copy.deepcopy(records[0])
record['page_updated_at'] = '2026-01-01'
record['history'][0]['date'] = '2026-02-01'
try:
    module.validate_record(record, set(), date(2026, 12, 31))
except module.ValidationError:
    pass
else:
    raise AssertionError('Se admitió historial posterior a la actualización')
record = copy.deepcopy(records[0])
record['history'][0]['date'] = '2099-01-01'
try:
    module.validate_record(record, set(), date(2026, 12, 31))
except module.ValidationError:
    pass
else:
    raise AssertionError('Se admitió historial futuro')
print('editoriales history chronology: OK')
