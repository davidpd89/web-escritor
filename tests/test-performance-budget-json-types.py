from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('budget_types', ROOT / 'scripts/check-performance-budgets.py')
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

for section in ['limits', 'baseline']:
    for invalid in [True, False, None, 1.25, '100', -1]:
        manifest = {
            'schema_version': 1,
            'enforcement': 'enforce',
            'budgets': [{
                'id': 'adversarial',
                'entrypoints': ['assets/main.js'],
                section: {'total_bytes': invalid}
            }]
        }
        errors = module.validate_manifest(manifest)
        assert errors, f'{section}.total_bytes={invalid!r} fue aceptado incorrectamente'
        assert any('total_bytes' in str(error) for error in errors), errors

for valid in [0, 1, 1024]:
    manifest = {
        'schema_version': 1,
        'enforcement': 'enforce',
        'budgets': [{
            'id': 'valid',
            'entrypoints': ['assets/main.js'],
            'limits': {'total_bytes': valid}
        }]
    }
    assert module.validate_manifest(manifest) == [], valid
print('PASS: esquema rechaza valores no enteros en presupuestos')