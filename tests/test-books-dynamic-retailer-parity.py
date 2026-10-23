from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
FACTS = json.loads((ROOT/'editorial-facts.json').read_text(encoding='utf-8'))['books']['samuelEntreMundos']
HTML = (ROOT/'libros/samuel-entre-mundos/index.html').read_text(encoding='utf-8')
JS = (ROOT/'assets/samuel-buy-modal.js').read_text(encoding='utf-8')

urls = FACTS['purchaseUrls']
for name, authority in [('AMAZON_URL',urls['amazonEs']),('CASADELLIBRO_URL',urls['casaDelLibro'])]:
    match = re.search(r'const\s+'+name+r'\s*=\s*[\'\"]([^\'\"]+)',JS)
    assert match, f'Constante ausente: {name}'
    generated = match.group(1)
    if name == 'CASADELLIBRO_URL':
        assert generated.startswith(authority),f'{name}: ISBN o comercio distinto'
    else:
        assert generated == authority,f'{name}: deriva respecto a autoridad editorial'

purchase = HTML.split('id="comprar"',1)[1].split('</section>',1)[0]
assert urls['publisher'] in purchase,'Editorial ausente de opciones visibles'
assert urls['amazonEs'] in purchase,'Amazon visible no coincide con la autoridad'
assert urls['casaDelLibro'] in purchase,'Casa del Libro no conserva ISBN autorizado'
assert 'href="${AMAZON_URL}"' in JS,'El modal no utiliza su constante verificada'
assert re.search(r'href="\$\{AMAZON_URL\}"[^>]*rel="[^"]*sponsored[^\"]*nofollow[^\"]*noopener[^\"]*noreferrer',JS),'Afiliación dinámica sin atributos de seguridad'
assert '9791387659776' in HTML and FACTS['asin'] in urls['amazonEs']
print('PASS books dynamic retailer parity')
