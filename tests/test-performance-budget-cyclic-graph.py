from __future__ import annotations
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
script = ROOT / 'scripts/check-performance-budgets.py'
spec = importlib.util.spec_from_file_location('budget_cycles', script)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory(prefix='budget-cycles-') as directory:
    root = Path(directory)
    files = {
        'assets/a.js': "import './b.js';\nexport const a = 1;\n",
        'assets/b.js': "export { a } from './a.js';\n",
        'assets/main.js': "import './a.js';\nimport './b.js';\n",
        'assets/a.css': '@import "./b.css";\n.a{}\n',
        'assets/b.css': '@import "./a.css";\n.b{}\n',
    }
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
    graph, errors = module.collect_graph(root, ['assets/main.js', 'assets/a.css'])
    assert errors == [], errors
    actual = {path.relative_to(root).as_posix() for path in graph}
    assert actual == set(files), (actual, files)
    assert len(graph) == len(files)
    metrics = module.metrics_for(graph)
    assert metrics['request_count'] == 5, metrics
    assert metrics['total_bytes'] == sum(path.stat().st_size for path in graph)
print('PASS: ciclos y dependencias compartidas contabilizados una sola vez')