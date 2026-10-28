#!/usr/bin/env python3
from __future__ import annotations
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
files = subprocess.check_output(['git', 'ls-files', '-z', '*.css'], cwd=ROOT).decode().split('\0')
URL_RE = re.compile(r'url\(\s*[\x22\x27]?([^\x22\x27)]+)[\x22\x27]?\s*\)', re.I)
IMPORT_RE = re.compile(r'@import\s+[\x22\x27]([^\x22\x27]+)[\x22\x27]', re.I)
errors = []
checked = 0

def resolve(ref, source):
    value = ref.strip()
    if not value or value.startswith(('#', '//', 'data:', 'blob:', 'var(')):
        return None
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc:
        return None
    raw = unquote(parsed.path)
    if not raw or '${' in raw:
        return None
    return ROOT / raw.lstrip('/') if raw.startswith('/') else source.parent / raw

for rel in files:
    if not rel:
        continue
    source = ROOT / rel
    css = re.sub(r'/\*[\s\S]*?\*/', '', source.read_text(encoding='utf-8'))
    refs = URL_RE.findall(css) + IMPORT_RE.findall(css)
    for ref in refs:
        target = resolve(ref, source)
        if target is None:
            continue
        checked += 1
        if not target.is_file():
            errors.append(f'{rel}: {ref} -> {target}')
assert checked >= 10, f'Auditoría vacía: {checked} referencias'
assert not errors, '\n'.join(errors[:100])
print(f'PASS CSS resource graph: {checked} referencias en {len(files)} hojas')
