#!/usr/bin/env python3
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

shell = load('qa_shell_context', 'scripts/build-site-shell.py')
context = load('qa_context_nav', 'scripts/build-section-context-nav.py')
pages, _ = shell.collect_shell_pages(ROOT)
checked = 0
errors = []
for path in pages:
    relative = path.relative_to(ROOT).as_posix()
    original = path.read_text(encoding='utf-8')
    first = context.apply_page(original, relative)
    if first is None:
        continue
    checked += 1
    second = context.apply_page(first, relative)
    if second != first:
        errors.append(f'{relative}: navegación no idempotente')
    if first.count('class="section-context"') != 1:
        errors.append(f'{relative}: número incorrecto de barras')
    if first.count(context.NAV_START) != 1 or first.count(context.NAV_END) != 1:
        errors.append(f'{relative}: delimitadores inconsistentes')
assert checked >= 10, f'Solo se encontraron {checked} contextos'
assert not errors, '\n'.join(errors)
print(f'PASS: {checked} navegaciones contextuales idempotentes')
