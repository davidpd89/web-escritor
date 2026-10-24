from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
PAGES=['index.html','empieza-aqui/index.html','mapa-del-sitio/index.html']


def block(html,name):
    pattern=r'<!-- site-shell:'+re.escape(name)+r':start\b[^>]*-->[\s\S]*?<!-- site-shell:'+re.escape(name)+r':end -->'
    matches=re.findall(pattern,html)
    assert len(matches)==1,(name,len(matches))
    return matches[0]

pages={p:(ROOT/p).read_text(encoding='utf-8') for p in PAGES}
for component in ['header','footer']:
    reference=block(pages[PAGES[0]],component)
    for pathname in PAGES[1:]:
        actual=block(pages[pathname],component)
        assert actual==reference,f'{pathname}: deriva del bloque generado {component}'
print('PASS navigation generated shell parity')
