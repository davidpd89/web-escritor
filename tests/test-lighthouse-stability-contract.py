import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ci = json.loads((ROOT / 'lighthouserc.json').read_text(encoding='utf-8'))['ci']
assert ci['collect']['numberOfRuns'] >= 3, 'Insufficient Lighthouse repetitions'
for matrix in ci['assert']['assertMatrix']:
    assertions = matrix['assertions']
    cls = assertions.get('cumulative-layout-shift')
    assert isinstance(cls, list) and len(cls) == 2, 'Missing CLS threshold'
    assert cls[0] == 'error', 'CLS must be enforced'
    assert cls[1]['maxNumericValue'] <= 0.1, 'CLS threshold too permissive'
    assert cls[1]['aggregationMethod'] == 'pessimistic', 'CLS must use pessimistic aggregation'
print('PASS: Lighthouse stability contract')