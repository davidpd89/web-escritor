from __future__ import annotations
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('budget_paths', ROOT / 'scripts/check-performance-budgets.py')
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory(prefix='budget-boundaries-') as directory:
    base = Path(directory)
    root = base / 'site'
    root.mkdir()
    (base / 'secret.js').write_text('export const secret = 1;', encoding='utf-8')
    (root / 'entry.js').write_text("import '../secret.js';\n", encoding='utf-8')
    graph, errors = module.collect_graph(root, ['entry.js'])
    assert any('escapa del repositorio' in error for error in errors), errors
    assert {p.name for p in graph} == {'entry.js'}, graph
    graph, errors = module.collect_graph(root, ['../secret.js'])
    assert any('fuera del repositorio' in error for error in errors), errors
    assert graph == [], graph
    assert module.resolve_local(root, root / 'entry.js', 'https://example.invalid/a.js') is None
    assert module.resolve_local(root, root / 'entry.js', 'data:text/javascript,abc') is None
print('PASS: dependencias externas al repositorio rechazadas')