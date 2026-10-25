from __future__ import annotations
import importlib.util
import re
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('zone_publisher_llms', ROOT / 'scripts/build-public-dist.py')
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)

content = (ROOT / 'llms.txt').read_text(encoding='utf-8')
urls = re.findall(r'https://davidportodiaz\.com/[^\s<>)]*', content)
assert urls, 'No se encontraron URL oficiales'
errors = []
for raw in urls:
    url = raw.rstrip('.,;')
    parsed = urlsplit(url)
    path = unquote(parsed.path).lstrip('/')
    candidates = ['index.html'] if not path else ([path + 'index.html'] if path.endswith('/') else [path, path + '/index.html'])
    existing = [rel for rel in candidates if (ROOT / rel).is_file()]
    if not existing:
        errors.append(f'Ruta inexistente: {url}')
    elif not any(publisher.is_publishable(rel, ROOT) for rel in existing):
        errors.append(f'Ruta no publicable: {url}')
assert not errors, '\n'.join(errors)
print(f'PASS llms official links: {len(urls)} referencias verificadas')
