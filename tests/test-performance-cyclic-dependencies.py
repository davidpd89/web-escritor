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
    (assets / 'a.js').write_text("import './b.js';\n", encoding='utf-8')
    (assets / 'b.js').write_text("import './a.js';\n", encoding='utf-8')
    (assets / 'a.css').write_text('@import "./b.css";\n', encoding='utf-8')
    (assets / 'b.css').write_text('@import "./a.css";\n', encoding='utf-8')
    files, errors = module.collect_graph(root, ['assets/a.js', 'assets/a.css'])
    assert not errors, errors
    assert len(files) == 4
    assert module.metrics_for(files)['request_count'] == 4
print('PASS: cyclic dependency graph')