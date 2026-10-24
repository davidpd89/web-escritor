from __future__ import annotations
import copy
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('radar_collision_exploratory', ROOT / 'scripts/build-radar-opportunities.py')
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
data = ROOT / 'data/radar-opportunities.json'
items = module.load_items(data)
watchlist = module.load_watchlist(data)
assert items and watchlist, 'Se necesitan ambas colecciones para probar la colisión'
mutated = copy.deepcopy(watchlist)
mutated[0]['id'] = items[0]['id']
try:
    module.ensure_disjoint_ids(items, mutated)
except ValueError:
    pass
else:
    raise AssertionError('Colisión entre items y watchlist admitida')
module.ensure_disjoint_ids(items, watchlist)
print('radar cross-list collision: OK')
