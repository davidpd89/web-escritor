from pathlib import Path
import re
from html import unescape

ROOT = Path(__file__).resolve().parents[1]
html = (ROOT/'libros/index.html').read_text(encoding='utf-8')
main = html.split('<main ',1)[1].split('</main>',1)[0]
articles = re.findall(r'<article\s+class="([^"]*books-stage[^"]*)"([^>]*)>(.*?)</article>',main,re.S)
assert len(articles)>=4,'Se esperaban novelas y colaboraciones editoriales'
expected = {'Las manecillas del recuerdo':'/las-manecillas-del-recuerdo/','Samuel entre mundos':'/libros/samuel-entre-mundos/'}
seen = set()
for classes, attrs, body in articles:
    heading = re.search(r'<h2[^>]*>(.*?)</h2>',body,re.S)
    assert heading,'Tarjeta sin título'
    title = unescape(re.sub(r'<[^>]*>','',heading.group(1))).strip()
    primary = re.findall(r'<a\b[^>]*class="[^"]*primary-action[^"]*"[^>]*href="([^"]+)"',body)
    assert len(primary)==1,f'{title}: debe existir un CTA principal único'
    assert title not in seen,f'Tarjeta duplicada: {title}'
    seen.add(title)
    if title in expected:
        assert 'books-stage-anthology' not in classes,f'{title}: novela clasificada como antología'
        assert primary[0]==expected[title],f'{title}: CTA apunta a obra equivocada'
    else:
        assert 'books-stage-anthology' in classes,f'{title}: colaboración presentada como novela individual'
        assert re.search(r'participaci[oó]n|relato|microrrelato',body,re.I),f'{title}: no identifica la participación'
assert set(expected).issubset(seen),'Falta una novela publicada'
print('PASS books editorial card intent')
