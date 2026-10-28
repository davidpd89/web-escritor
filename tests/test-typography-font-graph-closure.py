#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('budgets', ROOT / 'scripts/check-performance-budgets.py')
budgets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(budgets)

def test_font_graph_closure():
    manifest = json.loads((ROOT / 'data/performance-budgets.json').read_text(encoding='utf-8'))
    shell = next((item for item in manifest['budgets'] if item['id'] == 'shell-v1'), None)
    assert shell, 'data/performance-budgets.json: falta shell-v1'
    files, errors = budgets.collect_graph(ROOT, shell['entrypoints'])
    assert not errors, f'shell-v1: {errors}'
    included = set(files)
    referenced = set()
    css_files = [p for p in files if p.suffix == '.css']
    assert css_files, 'shell-v1: no se han encontrado hojas CSS'
    for css in css_files:
        content = css.read_text(encoding='utf-8')
        for dependency in budgets.local_dependencies(ROOT, css, content):
            if dependency.suffix.lower() not in {'.woff', '.woff2', '.ttf', '.otf'}:
                continue
            referenced.add(dependency)
            assert dependency in included, f'{css.relative_to(ROOT)}: fuente fuera del presupuesto: {dependency}'
            assert dependency.is_file(), f'{css.relative_to(ROOT)}: fuente inexistente: {dependency}'
    assert referenced, 'shell-v1: ninguna fuente encontrada; comprobar los CSS reales del grafo'
    measured = budgets.metrics_for(files)
    expected = sum(budgets.served_size(path) for path in referenced)
    assert measured['font_bytes'] == expected, f'shell-v1: font_bytes={measured["font_bytes"]}; fuentes reales={expected}'
    assert measured['request_count'] == len(included), f'shell-v1: peticiones={measured["request_count"]}; recursos={len(included)}'

if __name__ == '__main__':
    test_font_graph_closure()
