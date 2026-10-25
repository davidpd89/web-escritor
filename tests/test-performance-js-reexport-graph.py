import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location('budgets', ROOT / 'scripts/check-performance-budgets.py')
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    assets = root / 'assets'
    assets.mkdir()
    (assets / 'main.mjs').write_text("import './side.mjs';\nexport { value } from './barrel.mjs';\n", encoding='utf-8')
    (assets / 'barrel.mjs').write_text("export * from './shared.mjs';\n", encoding='utf-8')
    (assets / 'side.mjs').write_text("import { value } from './shared.mjs';\n", encoding='utf-8')
    (assets / 'shared.mjs').write_text('export const value = 42;\n', encoding='utf-8')
    files, errors = module.collect_graph(root, ['assets/main.mjs'])
    assert not errors, errors
    assert {p.name for p in files} == {'main.mjs', 'side.mjs', 'barrel.mjs', 'shared.mjs'}
    assert module.metrics_for(files)['request_count'] == 4
print('PASS: shared JS reexport graph')