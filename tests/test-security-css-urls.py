#!/usr/bin/env python3
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
files = subprocess.check_output(['git', 'ls-files', '-z', '*.css'], cwd=ROOT).decode().split('\0')
files = [p for p in files if p and (p == 'styles.css' or p.startswith(('assets/', 'accesibilidad/')))]
assert files, 'No hay hojas CSS públicas'
errors = []
patterns = {
    'script-url': re.compile(r'(?i)(?:javascript|vbscript)\s*:'),
    'http-url': re.compile(r'(?i)url\s*\(\s*[\x27\x22]?http://'),
    'expression': re.compile(r'(?i)\bexpression\s*\('),
    'binding': re.compile(r'(?i)(?<![\w-])(?:-moz-binding|behavior)\s*:'),
    'remote-import': re.compile(r'(?i)@import\s+(?:url\s*\()?\s*[\x27\x22]?(?:https?:)?//'),
}
for rel in files:
    source = (ROOT / rel).read_text(encoding='utf-8')
    source = re.sub(r'/\*.*?\*/', '', source, flags=re.S)
    for label, pattern in patterns.items():
        for match in pattern.finditer(source):
            line = source.count('\n', 0, match.start()) + 1
            errors.append(f'{rel}:{line}: {label}')
assert not errors, '\n'.join(errors[:100])
print(f'PASS CSS security: {len(files)} hojas')
