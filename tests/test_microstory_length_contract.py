from pathlib import Path
from html import unescape
import json
import re

ROOT=Path(__file__).resolve().parents[1]
page=(ROOT/'al-otro-lado/index.html').read_text(encoding='utf-8')
awards=(ROOT/'premios.html').read_text(encoding='utf-8')
match=re.search(r'<div class="microstory-text">\s*<p>(.*?)</p>',page,re.S)
assert match, 'No se localiza el texto íntegro'
text=unescape(re.sub(r'<[^>]+>','',match.group(1))).strip()
words=len(text.split())
characters=len(text)
credit=re.search(r'(\d+) palabras, (\d+) caracteres',page)
assert credit, 'Falta crédito numérico'
assert (words,characters)==tuple(map(int,credit.groups()))
assert characters<=500, f'Excede máximo del certamen: {characters}'
jsonld=json.loads(page.split('<script type="application/ld+json">',1)[1].split('</script>',1)[0])
story=next(x for x in jsonld['@graph'] if x['@type']=='ShortStory')
assert story['wordCount']==words
assert f'{words} palabras' in awards
assert f'{words} palabras' in page
assert '78 palabras' in page, 'Control histórico del texto premiado'
assert words==78 and characters==486
assert len((text+' palabra').split())!=words, 'La mutación de una palabra debe alterar el recuento'
assert len(text+'x')!=characters, 'La mutación de un carácter debe alterar el recuento'
print('PASS microstory length and published claims')
