from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit
import json
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://davidportodiaz.com'
class Head(HTMLParser):
    def __init__(self):
        super().__init__(); self.meta={}; self.links=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag=='meta':
            key=d.get('property') or d.get('name')
            if key: self.meta[key]=d.get('content','')
        if tag=='link': self.links.append(d)

for rel,url,kind,cover_name in [
    ('libros/index.html','/libros/','website','Las manecillas del recuerdo'),
    ('libros/samuel-entre-mundos/index.html','/libros/samuel-entre-mundos/','book','Samuel entre mundos')
]:
    source=(ROOT/rel).read_text(encoding='utf-8')
    head=source.split('</head>',1)[0]
    parser=Head(); parser.feed(head)
    m=parser.meta
    canonical=[x['href'] for x in parser.links if x.get('rel')=='canonical']
    assert canonical==[BASE+url],f'{rel}: canonical inconsistente'
    assert m.get('og:url')==canonical[0]
    assert m.get('og:type')==kind
    assert m.get('twitter:card')=='summary_large_image'
    assert m.get('og:title') and m.get('twitter:title')
    for prop in ['og:image','twitter:image']:
        image=m.get(prop,'')
        parts=urlsplit(image)
        assert image.startswith(BASE+'/assets/') and parts.netloc=='davidportodiaz.com'
        assert (ROOT/parts.path.lstrip('/')).is_file(),f'{rel}: falta imagen social {image}'
    assert cover_name.lower() in m.get('og:image:alt','').lower()
    docs=[json.loads(raw) for raw in re.findall(r'<script\s+type="application/ld\+json">(.*?)</script>',head,re.S)]
    graph=[node for doc in docs for node in doc.get('@graph',[doc])]
    expected='CollectionPage' if kind=='website' else 'WebPage'
    assert any(node.get('@type')==expected and node.get('url')==canonical[0] for node in graph)
print('PASS books social identity')
