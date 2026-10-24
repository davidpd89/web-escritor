from pathlib import Path
from urllib.parse import urlsplit,unquote
import re

ROOT=Path(__file__).resolve().parents[1]
script=(ROOT/'script.js').read_text(encoding='utf-8')
assert 'const items = [' in script
items=script.split('const items = [',1)[1].split('];',1)[0]
hrefs=re.findall(r'href:\s*"([^"]+)"',items)
assert len(hrefs)==5,f'Se esperaban cinco accesos moviles, encontrados {hrefs}'
for href in hrefs:
    parsed=urlsplit(href)
    route=parsed.path
    if route=='/':
        target=ROOT/'index.html'
    elif route.endswith('/'):
        target=ROOT/route.lstrip('/')/'index.html'
    else:
        target=ROOT/route.lstrip('/')
    assert target.is_file(),f'{href}: documento inexistente'
    if parsed.fragment:
        source=target.read_text(encoding='utf-8')
        target_id=unquote(parsed.fragment)
        assert re.search(r'\bid=["\']'+re.escape(target_id)+r'["\']',source),f'{href}: fragmento inexistente'
print(f'PASS dynamic navigation links: {len(hrefs)} routes')
