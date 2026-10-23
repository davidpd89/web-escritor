from pathlib import Path
from html import unescape
import re

ROOT=Path(__file__).resolve().parents[1]
index=(ROOT/'libros/index.html').read_text(encoding='utf-8')
samuel=(ROOT/'libros/samuel-entre-mundos/index.html').read_text(encoding='utf-8')

stages=re.findall(r'<article\s+class="[^"]*books-stage[^"]*"[^>]*>(.*?)</article>',index,re.S)
assert len(stages)>=4
for number,stage in enumerate(stages,1):
    headings=re.findall(r'<h2\b[^>]*>(.*?)</h2>',stage,re.S)
    assert len(headings)==1,f'Tarjeta {number}: encabezado ausente o duplicado'
    assert re.sub('<[^>]+>','',headings[0]).strip()

sections=re.findall(r'<section\s+class="[^"]*samuel-section[^"]*"[^>]*>(.*?)</section>',samuel,re.S)
assert len(sections)>=12,'Capítulos editoriales de Samuel desaparecidos'
for number,section in enumerate(sections,1):
    match=re.search(r'<header\s+class="samuel-section__head"[^>]*>(.*?)</header>',section,re.S)
    assert match,f'Sección {number} sin cabecera editorial'
    headings=re.findall(r'<h2\b[^>]*>(.*?)</h2>',match.group(1),re.S)
    assert len(headings)==1,f'Sección {number} sin H2 propio'

for doc in [index,samuel]:
    for value in re.findall(r'aria-labelledby="([^"]+)"',doc):
        for ident in value.split():
            assert re.search(r'\bid="'+re.escape(ident)+r'"',doc),f'aria-labelledby apunta a un ID inexistente: {ident}'
quiz=re.search(r'<div\s+class="quiz-wrap"([^>]*)>',samuel)
assert quiz and 'role="region"' in quiz.group(1)
label=re.search(r'aria-label="([^"]+)"',quiz.group(1))
assert label and 'Noveris' in unescape(label.group(1))
assert 'id="recursos-title"' in index and 'aria-labelledby="recursos-title"' in index
print('PASS books region heading association')
