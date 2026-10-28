import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location('budgets', ROOT / 'scripts/check-performance-budgets.py')
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

for invalid in [True, False, 1.5, '100', None, -1]:
    manifest = {
        'schema_version': 1,
        'enforcement': 'enforce',
        'budgets': [{
            'id': 'demo',
            'entrypoints': ['assets/app.js'],
            'limits': {'total_bytes': invalid}
        }]
    }
    errors = module.validate_manifest(manifest)
    assert errors, f'Invalid limit accepted: {invalid!r}'

for invalid in [True, '1', 1.0, None]:
    manifest = {
        'schema_version': invalid,
        'enforcement': 'report',
        'budgets': [{'id': 'demo', 'entrypoints': ['assets/app.js']}]
    }
    assert module.validate_manifest(manifest), f'Invalid schema version accepted: {invalid!r}'
print('PASS: strict budget schema types')