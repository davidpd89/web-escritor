#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'publicar-web/index.html'
data = path.read_bytes()
text = data.decode('utf-8')

MAX_DOCUMENT_BYTES = 4096
assert len(data) <= MAX_DOCUMENT_BYTES, f'HTML demasiado pesado: {len(data)} bytes'
assert '<main' in text.lower(), 'Falta contenido principal'
assert not re.search(r'<script\b', text, re.I), 'El checklist estático incorpora JavaScript'

resource_tags = re.findall(r'<(?:script|img|iframe|link)\b[^>]*>', text, re.I)
for tag in resource_tags:
    assert not re.search(r'<iframe\b', tag, re.I), f'Frame inesperado: {tag}'
    if re.match(r'<link\b', tag, re.I):
        canonical = re.search(r'\brel\s*=\s*(["\'])canonical\1', tag, re.I)
        if canonical:
            assert not re.search(r'\bsrc\s*=\s*["\']https?://', tag, re.I), f'Recurso remoto: {tag}'
            continue
    assert not re.search(r'\b(?:src|href)\s*=\s*["\']https?://', tag, re.I), f'Recurso remoto: {tag}'

print(f'PASS publicar-web: {len(data)} bytes, sin recursos remotos de renderizado')
