#!/usr/bin/env python3
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
files = sorted((ROOT / 'assets').glob('*.css'))
assert files, 'No se encontraron estilos'
graph = {}
errors = []
for file in files:
    deps = []
    text = file.read_text(encoding='utf-8')
    for literal in re.findall(r'@import\s+url\(([^)]+)\)', text):
        raw = literal.strip().strip('\x22\x27')
        url = urlsplit(raw)
        if url.scheme or url.netloc:
            continue
        dep = (ROOT / url.path.lstrip('/')) if url.path.startswith('/') else (file.parent / url.path)
        dep = dep.resolve()
        deps.append(dep)
        if not dep.is_file():
            errors.append(f'{file.name}: import inexistente {raw}')
    if len(deps) != len(set(deps)):
        errors.append(f'{file.name}: imports duplicados')
    graph[file.resolve()] = deps
visiting = set()
visited = set()
def visit(node):
    if node in visiting:
        errors.append(f'Ciclo CSS detectado: {node}')
        return
    if node in visited:
        return
    visiting.add(node)
    for child in graph.get(node, []):
        visit(child)
    visiting.remove(node)
    visited.add(node)
for file in graph:
    visit(file)
assert not errors, '\n'.join(errors)
print(f'OK grafo CSS: {len(files)} hojas analizadas')
