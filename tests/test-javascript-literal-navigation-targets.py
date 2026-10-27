#!/usr/bin/env python3
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = [
    re.compile(r'''\.href\s*=\s*['\"](/[^'\"]+)['\"]'''),
    re.compile(r'''(?:location\.assign|location\.replace|window\.open)\s*\(\s*['\"](/[^'\"]+)['\"]'''),
]
SKIP = ('/api/', '/cdn-cgi/')
names = subprocess.check_output(['git', 'ls-files', '-z', '*.js', '*.mjs'], cwd=ROOT).decode().split('\0')
errors = []
checked = 0
for name in names:
    if not name or not (name == 'script.js' or name.startswith('assets/')):
        continue
    text = (ROOT / name).read_text(encoding='utf-8')
    for pattern in PATTERNS:
        for match in pattern.finditer(text):
            value = match.group(1)
            if value.startswith(SKIP) or '${' in value:
                continue
            path = unquote(urlsplit(value).path)
            if not path:
                continue
            checked += 1
            dest = ROOT / path.lstrip('/')
            if path == '/' or path.endswith('/'):
                dest = dest / 'index.html'
            elif not dest.is_file() and not Path(path).suffix:
                dest = dest / 'index.html'
            if not dest.is_file():
                errors.append(f'{name}: {value}')
assert checked > 0, 'No se inspeccionó ninguna navegación JS'
assert not errors, '\n'.join(errors)
print(f'PASS JavaScript navigation literals: {checked}')
