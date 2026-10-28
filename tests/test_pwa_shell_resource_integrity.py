from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
sw = (ROOT / 'service-worker.js').read_text(encoding='utf-8')
match = re.search(r'const APP_SHELL\s*=\s*\[([^\]]+)\]', sw, re.S)
assert match, 'service-worker.js: no se encuentra la lista de recursos APP_SHELL'
urls = re.findall(r'[\"\'](/[^\"\']+)[\"\']', match.group(1))
assert urls, 'service-worker.js: APP_SHELL no contiene recursos'
assert len(urls) == len(set(urls)), 'service-worker.js: recursos duplicados en APP_SHELL'
for url in urls:
    assert '?' not in url and '#' not in url, f'APP_SHELL: recurso no canónico {url}'
    path = ROOT / url.lstrip('/')
    assert path.is_file(), f'APP_SHELL: recurso inexistente {url}'
    assert path.stat().st_size > 0, f'APP_SHELL: recurso vacío {url}'
print(f'PASS: {len(urls)} recursos de APP_SHELL disponibles')
