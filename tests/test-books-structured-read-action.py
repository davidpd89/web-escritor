from pathlib import Path
from urllib.parse import urlsplit
import json
import re

ROOT=Path(__file__).resolve().parents[1]
book=(ROOT/'libros/samuel-entre-mundos/index.html').read_text(encoding='utf-8')
catalog=(ROOT/'libros/index.html').read_text(encoding='utf-8')
docs=[json.loads(s) for s in re.findall(r'<script\s+type="application/ld\+json">(.*?)</script>',book,re.S)]
graph=[item for doc in docs for item in doc.get('@graph',[doc])]
books=[item for item in graph if item.get('@type')=='Book']
assert len(books)==1,'La ficha debe describir una obra principal'
action=books[0].get('potentialAction',{})
assert action.get('@type')=='ReadAction','Falta la acción semántica de lectura gratuita'
target=action.get('target','')
parts=urlsplit(target)
assert parts.scheme=='https' and parts.netloc=='davidportodiaz.com'
assert parts.path.endswith('/') and not parts.query and not parts.fragment
assert (ROOT/parts.path.lstrip('/')/'index.html').is_file(),f'ReadAction sin documento: {target}'
for source,selector in [(book,r'<a\s+class="primary-action"\s+href="([^"]+)"[^>]*>Leer capítulo 1 gratis</a>'),(catalog,r'<a\s+class="text-action"\s+href="([^"]+)"[^>]*>Leer capítulo 1</a>')]:
    match=re.search(selector,source)
    assert match,'Falta CTA visible de lectura gratuita'
    assert match.group(1)==parts.path,f'CTA visible diverge de ReadAction: {match.group(1)}'
print('PASS books structured read action')
