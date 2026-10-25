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
    (assets / 'main.css').write_text('''@import url("./a.css");
@import './b.css';
@import url('./c.css');
@import "./a.css";
''', encoding='utf-8')
    for name in ('a.css', 'b.css', 'c.css'):
        (assets / name).write_text('body { display: block; }', encoding='utf-8')
    files, errors = module.collect_graph(root, ['assets/main.css'])
    assert not errors, errors
    names = {p.name for p in files}
    assert names == {'main.css', 'a.css', 'b.css', 'c.css'}, names
    assert module.metrics_for(files)['request_count'] == 4
print('PASS: CSS import coverage')