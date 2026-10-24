import importlib.util
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('radar_zone_numbers', ROOT / 'scripts/build-radar-opportunities.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
sample = dict(mod.load_items(ROOT / 'data/radar-opportunities.json')[0])

for value in (math.nan, math.inf, -math.inf):
    candidate = {**sample, 'fee_eur': value}
    try:
        mod.validate(candidate)
    except ValueError:
        continue
    raise AssertionError(f'fee_eur no finito aceptado: {value!r}')
print('radar finite fees: OK')
