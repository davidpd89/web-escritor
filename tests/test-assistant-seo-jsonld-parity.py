import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
main = (ROOT / 'asistente/index.html').read_text(encoding='utf-8')
embed = (ROOT / 'asistente/embed.html').read_text(encoding='utf-8')
canonical = 'https://davidportodiaz.com/asistente/'

assert re.search(r'<link\s+rel="canonical"\s+href="' + re.escape(canonical) + r'"', main)
assert 'content="noindex,nofollow"' in main
assert 'content="noindex,nofollow"' in embed
assert not re.search(r'<link\s+rel="canonical"', embed), 'El iframe no necesita URL canónica independiente'

blocks = re.findall(r'<script\s+type="application/ld\+json"[^>]*>(.*?)</script>', main, re.S)
assert len(blocks) >= 2, 'Faltan los datos estructurados del asistente'
objects = [json.loads(block) for block in blocks]
webpages = [x for x in objects if x.get('@type') == 'WebPage']
crumbs = [x for x in objects if x.get('@type') == 'BreadcrumbList']
assert len(webpages) == 1 and len(crumbs) == 1
assert webpages[0]['url'] == canonical
assert webpages[0]['@id'] == canonical
items = crumbs[0]['itemListElement']
assert [x['position'] for x in items] == list(range(1, len(items) + 1))
assert items[-1]['item'] == canonical
print('assistant-seo-jsonld-parity: OK')
