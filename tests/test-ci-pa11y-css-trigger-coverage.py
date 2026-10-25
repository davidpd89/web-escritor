#!/usr/bin/env python3
"""Verifica cobertura de rutas que disparan Pa11y."""
from pathlib import Path
import fnmatch
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / '.github/workflows/pa11y-baseline.yml').read_text(encoding='utf-8')
block = re.search(r'(?m)^  push:\s*\n(?P<body>(?:^    .*\n|^\s*\n)*)', workflow)
assert block, 'No existe trigger push'
match = re.search(r'(?m)^    paths:\s*\n(?P<body>(?:^      - .*\n)*)', block.group('body'))
assert match, 'Push no declara rutas'
patterns = []
for line in match.group('body').splitlines():
    value = line.strip()[2:].strip().strip("'\"")
    patterns.append(value)

def covers(path):
    for pattern in patterns:
        if pattern in ('**/*.html', '**/*.css') and path.endswith(pattern[-5:]):
            return True
        if fnmatch.fnmatchcase(path, pattern):
            return True
    return False

required = ['styles.css', 'assets/v1-shell.css', 'assets/v1-accessibility-statement.css', 'index.html', 'accesibilidad/index.html']
errors = [path for path in required if not covers(path)]
print(f'Pa11y triggers: {len(required)} rutas, {len(errors)} sin cobertura')
for path in errors:
    print('FAIL', path)
sys.exit(bool(errors))