#!/usr/bin/env python3
from pathlib import Path
from urllib.parse import urlsplit, unquote
import re

ROOT = Path(__file__).resolve().parents[1]
css_files = sorted((ROOT / 'assets').rglob('*.css')) + [ROOT / 'styles.css']
face_pattern = re.compile(r'@font-face\s*\{([^{}]*)\}', re.I | re.S)
url_pattern = re.compile(r'url\(\s*[\'\"]?([^\'\"\)]+)', re.I)
failures = []
faces = 0

for css in css_files:
    text = css.read_text(encoding='utf-8')
    for face in face_pattern.findall(text):
        faces += 1
        refs = url_pattern.findall(face)
        local_refs = re.findall(r'\blocal\s*\(\s*(?:"[^"]+"|\'[^\']+\'|[^)]+)\s*\)', face, re.I)
        if refs and not re.search(r'font-display\s*:\s*(?:swap|optional|fallback|block|auto)\s*(?:;|$)', face, re.I):
            failures.append(f'{css.relative_to(ROOT)}: font-display ausente')
        if not refs and not local_refs:
            failures.append(f'{css.relative_to(ROOT)}: font-face sin fuente local ni archivo')
        for ref in refs:
            url = urlsplit(ref.strip())
            if url.scheme or url.netloc or ref.startswith('//'):
                failures.append(f'{css.relative_to(ROOT)}: fuente externa {ref}')
                continue
            target = (ROOT / unquote(url.path).lstrip('/')).resolve() if url.path.startswith('/') else (css.parent / unquote(url.path)).resolve()
            if not target.is_relative_to(ROOT) or not target.is_file():
                failures.append(f'{css.relative_to(ROOT)}: fuente inexistente {ref}')

assert faces > 5, f'Inventario de fuentes insuficiente: {faces}'
assert not failures, '\n'.join(failures)
print(f'PASS {faces} reglas font-face')
