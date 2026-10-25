import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location('budgets', ROOT / 'scripts/check-performance-budgets.py')
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

with tempfile.TemporaryDirectory() as tmp:
    base = Path(tmp)
    root = base / 'site'
    root.mkdir()
    assets = root / 'assets'
    assets.mkdir()
    outside = base / 'outside.js'
    outside.write_text('export const secret = 1;', encoding='utf-8')
    (assets / 'main.js').write_text("import './external.js';", encoding='utf-8')
    (assets / 'external.js').symlink_to(outside)
    files, errors = module.collect_graph(root, ['assets/main.js'])
    assert errors, 'Symlink escape was accepted'
    assert outside.resolve() not in files
    assert any('fuera del repositorio' in error or 'escapa del repositorio' in error for error in errors), errors
print('PASS: symlink boundary')