#!/usr/bin/env python3
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PATTERN = re.compile(r'https://davidportodiaz\.com(?:/[^\s<>\)\]\"\']*)?')
failures = []
checked = 0

for source in ('llms.txt', 'llms-full.txt'):
    text = (ROOT / source).read_text(encoding='utf-8')
    links = set(match.group(0).rstrip('.,;') for match in PATTERN.finditer(text))
    assert links, f'{source} no contiene enlaces internos'

    for url in sorted(links):
        parsed = urlsplit(url)
        if parsed.hostname != 'davidportodiaz.com':
            continue
        relative = unquote(parsed.path).lstrip('/')
        target = ROOT / relative
        if not relative or parsed.path.endswith('/'):
            target = target / 'index.html'
        if not target.is_file():
            failures.append(f'{source}: falta {url} -> {target.relative_to(ROOT)}')
            continue
        checked += 1
        if parsed.fragment and target.suffix.lower() == '.html':
            html = target.read_text(encoding='utf-8')
            fragment = unquote(parsed.fragment)
            markers = (f'id="{fragment}"', f"id='{fragment}'", f'name="{fragment}"', f"name='{fragment}'")
            if not any(marker in html for marker in markers):
                failures.append(f'{source}: fragmento #{fragment} ausente en {url}')

assert checked >= 20, f'Cobertura demasiado pequeña: {checked}'
assert not failures, '\n'.join(failures)
print(f'OK: {checked} destinos internos de documentos LLM comprobados')
