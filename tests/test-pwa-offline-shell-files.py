import re
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parent.parent
source = (ROOT / 'service-worker.js').read_text(encoding='utf-8')
match = re.search(r'const APP_SHELL\s*=\s*\[([\s\S]*?)\];', source)
assert match, 'APP_SHELL declaration missing'
paths = re.findall(r'["\'](/[^"\']+)["\']', match.group(1))
assert paths, 'APP_SHELL empty'
assert len(paths) == len(set(paths)), 'Duplicate offline shell resources'
for path in paths:
    url = urlsplit(path)
    assert not url.query and not url.fragment, f'Unstable shell URL: {path}'
    resolved = (ROOT / unquote(url.path).lstrip('/')).resolve()
    assert resolved.is_relative_to(ROOT.resolve()), f'Path escape: {path}'
    assert resolved.is_file(), f'Missing offline resource: {path}'
print(f'PASS: {len(paths)} offline shell resources exist')