#!/usr/bin/env python3
"""Cobertura de movimiento reducido en estilos locales."""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
paths = subprocess.check_output(['git', 'ls-files', '*.css'], cwd=ROOT, text=True).splitlines()
errors = []
checked = 0
for rel in paths:
    if rel.startswith(('tests/', 'qa/', 'docs/', 'lab/')):
        continue
    if rel != 'styles.css' and not rel.startswith('assets/'):
        continue
    css = (ROOT / rel).read_text(encoding='utf-8', errors='replace')
    checked += 1
    animations = bool(re.search(r'animation(?:-name)?\s*:\s*(?!none\b)', css, re.I))
    smooth = bool(re.search(r'scroll-behavior\s*:\s*smooth', css, re.I))
    if not (animations or smooth):
        continue
    if 'prefers-reduced-motion' not in css:
        errors.append(f'{rel}: movimiento sin cobertura local de reduced-motion')
assert checked > 0
print(f'Reduced motion: {checked} CSS, {len(errors)} posibles huecos')
print('\n'.join(errors[:80]))
sys.exit(bool(errors))