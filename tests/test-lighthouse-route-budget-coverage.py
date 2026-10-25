import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
config = json.loads((ROOT / 'lighthouserc.json').read_text(encoding='utf-8'))['ci']
urls = config['collect']['url']
matrices = config['assert']['assertMatrix']
assert urls, 'No Lighthouse URLs configured'
assert matrices, 'No Lighthouse assertion matrices configured'
for url in urls:
    matches = [m for m in matrices if re.search(m['matchingUrlPattern'], url)]
    assert matches, f'No assertion matrix for {url}'
    keys = set().union(*(set(m['assertions']) for m in matches))
    for required in ('categories:performance', 'categories:accessibility', 'largest-contentful-paint'):
        assert required in keys, f'{url} missing {required}'
        assert any(m['assertions'].get(required) != 'off' for m in matches), f'{url}: {required} disabled'
print(f'PASS: Lighthouse coverage for {len(urls)} routes')