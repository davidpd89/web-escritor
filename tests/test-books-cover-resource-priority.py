from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
class Images(HTMLParser):
    def __init__(self):
        super().__init__(); self.images=[]; self.preloads=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='img': self.images.append(a)
        if tag=='link' and a.get('rel')=='preload' and a.get('as')=='image': self.preloads.append(a)

for rel in ['libros/index.html','libros/samuel-entre-mundos/index.html']:
    html=(ROOT/rel).read_text(encoding='utf-8')
    main=html.split('<main ',1)[1].split('</main>',1)[0]
    images=Images(); images.feed(main)
    assert len(images.images)>=3,f'{rel}: inventario gráfico reducido'
    hero=images.images[0]
    assert hero.get('fetchpriority')=='high',f'{rel}: portada sin prioridad'
    assert hero.get('loading','eager')!='lazy',f'{rel}: portada principal diferida'
    eager=[img for img in images.images if img.get('loading','eager')!='lazy']
    assert eager==[hero],f'{rel}: demasiadas imágenes compitiendo por LCP'
    for img in images.images:
        assert int(img.get('width',0))>0 and int(img.get('height',0))>0,f'{rel}: dimensiones ausentes'
        assert img.get('alt','').strip(),f'{rel}: imagen informativa sin descripción'
        src=urlsplit(img.get('src','')).path
        assert src.startswith('/assets/') and (ROOT/src.lstrip('/')).is_file(),f'{rel}: recurso inexistente {src}'
    head=Images(); head.feed(html.split('</head>',1)[0])
    if rel.endswith('samuel-entre-mundos/index.html'):
        assert any(urlsplit(p.get('href','')).path==urlsplit(hero['src']).path for p in head.preloads),'Samuel: preload no coincide con portada real'
print('PASS books resource priority')
