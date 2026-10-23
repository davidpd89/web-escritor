#!/usr/bin/env python3
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('budgets', ROOT / 'scripts/check-performance-budgets.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
manifest = json.loads((ROOT / 'data/performance-budgets.json').read_text(encoding='utf-8'))
registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))

class Assets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
    def handle_starttag(self, tag, attributes):
        a = dict(attributes)
        if tag == 'script' and a.get('src'):
            self.refs.append(a['src'])
        elif tag == 'link' and 'stylesheet' in (a.get('rel') or '').lower().split():
            self.refs.append(a.get('href', ''))

covered = set()
for budget in manifest['budgets']:
    files, errors = module.collect_graph(ROOT, budget['entrypoints'])
    assert not errors, f'{budget["id"]}: {errors}'
    covered.update(path.relative_to(ROOT).as_posix() for path in files)

used = set()
for entry in registry['entries']:
    if entry.get('status', registry['defaults'].get('status')) != 'public':
        continue
    rel = entry.get('sourceFile', '')
    if not rel.endswith('.html'):
        continue
    page = ROOT / rel
    assert page.is_file(), rel
    parser = Assets()
    parser.feed(page.read_text(encoding='utf-8'))
    for ref in parser.refs:
        url = urlsplit(ref)
        if url.scheme or url.netloc or not url.path:
            continue
        target = (ROOT / unquote(url.path).lstrip('/')).resolve() if url.path.startswith('/') else (page.parent / unquote(url.path)).resolve()
        if target.is_relative_to(ROOT) and target.is_file():
            used.add(target.relative_to(ROOT).as_posix())

missing = sorted(used - covered)
print(f'Assets usados={len(used)}; cubiertos={len(used & covered)}; no cubiertos={len(missing)}')
assert used, 'Inventario de assets vacío'
assert not missing, 'Assets sin presupuesto:\n' + '\n'.join(missing)
print('PASS cobertura presupuestaria')
