from __future__ import annotations
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('budget_fonts', ROOT / 'scripts/check-performance-budgets.py')
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory(prefix='budget-fonts-') as directory:
    root = Path(directory)
    css = root / 'assets/site.css'
    font = root / 'assets/fonts/main.woff2'
    font.parent.mkdir(parents=True)
    css.write_text('@font-face{font-family:Demo;src:url("./fonts/main.woff2") format("woff2")}body{font-family:Demo}', encoding='utf-8')
    font.write_bytes(b'FAKE-FONT-FIXTURE' * 32)
    graph, errors = module.collect_graph(root, ['assets/site.css'])
    assert errors == [], errors
    relative = {path.relative_to(root).as_posix() for path in graph}
    assert 'assets/site.css' in relative
    assert 'assets/fonts/main.woff2' in relative, 'La fuente crítica queda invisible para el presupuesto'
    metrics = module.metrics_for(graph)
    assert metrics['font_bytes'] == len(font.read_bytes()), metrics
    assert metrics['request_count'] == 2, metrics
print('PASS: presupuesto incluye fuentes locales referenciadas desde CSS')