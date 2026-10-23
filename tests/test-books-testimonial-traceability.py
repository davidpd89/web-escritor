from pathlib import Path
from html import unescape
import json
import re

ROOT=Path(__file__).resolve().parents[1]
html=(ROOT/'libros/samuel-entre-mundos/index.html').read_text(encoding='utf-8')
facts=json.loads((ROOT/'editorial-facts.json').read_text(encoding='utf-8'))['books']['samuelEntreMundos']
section=html.split('id="validacion-social"',1)[1].split('</section>',1)[0]
stream=re.search(r'<ul\s+class="samuel-proof__stream">(.*?)</ul>',section,re.S)
assert stream,'Listado de testimonios ausente'
pairs=re.findall(r'<blockquote>(.*?)</blockquote>\s*<cite>(.*?)</cite>',stream.group(1),re.S)
assert len(pairs)>=5,'Se ha reducido el inventario de testimonios'
seen=set()
for quote,citation in pairs:
    content=unescape(re.sub(r'<[^>]+>','',quote)).strip(' \n\t«»')
    author=unescape(re.sub(r'<[^>]+>','',citation)).strip()
    assert len(content)>=30,'Testimonio vacío o truncado'
    assert '· Amazon España' in author,'Atribución sin fuente comercial'
    assert author.split('·',1)[0].strip(),'Autor de reseña vacío'
    assert content not in seen,'Testimonio repetido'
    seen.add(content)
assert facts['asin'] in section,'La sección no mantiene la identidad del producto'
assert re.search(r'data-reader-review="amazon"[^>]*href="[^"]*'+re.escape(facts['asin'])+r'#customerReviews',section),'Falta acceso a las opiniones del mismo libro'
print('PASS books testimonial traceability')
