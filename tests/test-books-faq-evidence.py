from pathlib import Path
from html import unescape
import json
import re

ROOT = Path(__file__).resolve().parents[1]
html = (ROOT/'libros/samuel-entre-mundos/index.html').read_text(encoding='utf-8')
facts = json.loads((ROOT/'editorial-facts.json').read_text(encoding='utf-8'))['books']['samuelEntreMundos']
faq = html.split('id="faq"',1)[1].split('</section>',1)[0]
pairs = re.findall(r'<details>\s*<summary>(.*?)</summary>\s*<p>(.*?)</p>\s*</details>',faq,re.S)
assert len(pairs)>=7,'FAQ reducido inesperadamente'
questions = []
for question, answer in pairs:
    q = unescape(re.sub(r'<[^>]*>','',question)).strip()
    a = unescape(re.sub(r'<[^>]*>','',answer)).strip()
    assert q.endswith('?'),f'Pregunta mal identificada: {q}'
    assert len(a)>35,f'Respuesta insuficiente: {q}'
    assert 'Samuel' in a or 'Noveris' in a or 'David Porto Díaz' in a,f'Respuesta ajena a la obra: {q}'
    questions.append(q)
assert len(set(questions))==len(questions),'Preguntas duplicadas'
age = next(answer for q,answer in pairs if 'edad' in q.lower())
assert facts['typicalAgeRange'] is None,'El contrato presupone ausencia de rango oficial'
assert re.search(r'no publica un rango de edad oficial',age,re.I),'FAQ atribuye una edad oficial no verificada'
genre = next(answer for q,answer in pairs if 'romantasy' in q.lower())
assert re.search(r'No\.',genre),'FAQ cambia su clasificación editorial'
buy = next(answer for q,answer in pairs if 'comprar' in q.lower())
assert facts['purchaseUrls']['publisher'] in buy
assert facts['purchaseUrls']['amazonEs'] in buy
print('PASS books FAQ evidence')
