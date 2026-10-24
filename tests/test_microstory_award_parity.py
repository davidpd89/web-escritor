from pathlib import Path
from html import unescape
import re

ROOT=Path(__file__).resolve().parents[1]
story=(ROOT/'al-otro-lado/index.html').read_text(encoding='utf-8')
awards=(ROOT/'premios.html').read_text(encoding='utf-8')
record=re.search(r'<li data-award-record>.*?<h3 data-award-result>Primer Premio</h3>(.*?)</li>',awards,re.S)
assert record, 'Premio no identificado en la página matriz'
record=unescape(re.sub(r'<[^>]+>',' ',record.group(1)))
record=' '.join(record.split())
plain=unescape(re.sub(r'<[^>]+>',' ',story))
plain=' '.join(plain.split())
for term in ['David Porto Díaz','Letras Como Espada','XII Certamen de Microrrelatos','Al otro lado','20 de marzo de 2026','78 palabras']:
    assert term in record, f'Premios pierde: {term}'
    assert term in plain, f'Relato pierde: {term}'
assert 'Primer Premio' in record
assert 'Ganó el XII Certamen' in plain
assert '/al-otro-lado/' in awards
assert '/premios.html' in story
assert 'No es un premio de' in plain
assert 'No es un premio de' in record
print('PASS microstory award attribution parity')
