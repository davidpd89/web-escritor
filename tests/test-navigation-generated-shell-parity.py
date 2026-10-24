from pathlib import Path
import json
import re

ROOT=Path(__file__).resolve().parents[1]
PAGES=['index.html','empieza-aqui/index.html','mapa-del-sitio/index.html']


def block(html,name):
    pattern=r'<!-- site-shell:'+re.escape(name)+r':start\b[^>]*-->[\s\S]*?<!-- site-shell:'+re.escape(name)+r':end -->'
    matches=re.findall(pattern,html)
    assert len(matches)==1,(name,len(matches))
    return matches[0]

EXTRAS=json.loads((ROOT/'data/site-shell-extras.json').read_text(encoding='utf-8'))['footerNavExtras']


def without_declared_extras(html,pathname):
    # Enlaces contextuales declarados en data/site-shell-extras.json: se admiten
    # por pagina; cualquier otra diferencia sigue siendo deriva.
    for extra in EXTRAS.values():
        if pathname in extra['pages']:
            html=re.sub(r'<a href="/cuaderno/feed\.xml">RSS del Cuaderno</a>','',html)
    return html


pages={p:(ROOT/p).read_text(encoding='utf-8') for p in PAGES}
for component in ['header','footer']:
    reference=block(pages[PAGES[0]],component)
    for pathname in PAGES[1:]:
        actual=block(pages[pathname],component)
        if component=='footer':
            actual=without_declared_extras(actual,pathname)
        assert actual==reference,f'{pathname}: deriva del bloque generado {component}'
print('PASS navigation generated shell parity')
