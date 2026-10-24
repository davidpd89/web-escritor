#!/usr/bin/env python3
"""Punto fijo del shell sobre todas las páginas V1 controladas."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'scripts/build-site-shell.py'
spec = importlib.util.spec_from_file_location('shell_fixed_point', path)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

nav, registry, extras = mod.shell_sources()
pages, escapees = mod.collect_shell_pages(ROOT)
assert not escapees, escapees
assert len(pages) >= 40, 'Inventario de páginas V1 anormalmente pequeño'

failures = []
markers = [(mod.HEADER_START, mod.HEADER_END), (mod.DIALOG_START, mod.DIALOG_END), (mod.FOOTER_START, mod.FOOTER_END)]
for page in pages:
    rel = page.relative_to(ROOT).as_posix()
    original = page.read_text(encoding='utf-8')
    first = mod.apply_shell(original, rel, nav, registry, extras)
    second = mod.apply_shell(first, rel, nav, registry, extras)
    if first != second:
        failures.append(f'{rel}: segunda generación modifica HTML')
    for start, end in markers:
        if first.count(start) != 1 or first.count(end) != 1:
            failures.append(f'{rel}: marcadores duplicados o ausentes')

assert not failures, '\n'.join(failures)
print(f'PASS: {len(pages)} páginas V1 alcanzan punto fijo')
