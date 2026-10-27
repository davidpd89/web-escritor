import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pagefind_robots_extra', ROOT / 'scripts/build-pagefind-index.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

blocked = [
    '<meta name="googlebot" content="noindex,follow">',
    '<meta name="bingbot" content="NOINDEX">',
    '<meta name="robots" content="nofollow noindex">',
    '<META CONTENT="NOINDEX, FOLLOW" NAME="ROBOTS">'
]
allowed = [
    '<meta name="robots" content="index,follow">',
    '<meta name="description" content="noindex">',
    '<meta name="googlebot" content="index">'
]

for html in blocked:
    assert b.is_noindex('<head>' + html + '</head>'), f'Noindex ignorado: {html}'
for html in allowed:
    assert not b.is_noindex('<head>' + html + '</head>'), f'Falso bloqueo: {html}'

print('PASS: robots por agente')
