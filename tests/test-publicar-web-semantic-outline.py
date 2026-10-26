from html.parser import HTMLParser
from pathlib import Path

PAGE = Path(__file__).resolve().parents[1] / 'publicar-web/index.html'

class Outline(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.main_count = 0
        self.inside_main = False
        self.headings = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == 'main':
            self.main_count += 1
            self.inside_main = True
        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self.current = {'level': int(tag[1]), 'text': '', 'inside': self.inside_main}

    def handle_data(self, data):
        if self.current is not None:
            self.current['text'] += data

    def handle_endtag(self, tag):
        if self.current is not None and tag == 'h' + str(self.current['level']):
            self.headings.append(self.current)
            self.current = None
        if tag == 'main':
            self.inside_main = False

p = Outline()
p.feed(PAGE.read_text(encoding='utf-8'))
assert p.main_count == 1, f'{PAGE}: se esperaba un main; encontrados {p.main_count}'
assert p.headings, f'{PAGE}: documento sin encabezados'
assert p.headings[0]['level'] == 1, f'{PAGE}: el primer encabezado no es H1'
assert sum(h['level'] == 1 for h in p.headings) == 1, f'{PAGE}: cantidad incorrecta de H1'
for index, h in enumerate(p.headings):
    assert h['inside'], f'{PAGE}: encabezado {index + 1} fuera de main'
    assert h['text'].strip(), f'{PAGE}: encabezado {index + 1} vacío'
    if index:
        assert h['level'] <= p.headings[index - 1]['level'] + 1, f'{PAGE}: salto de nivel entre encabezados {index} y {index + 1}'
print(f'OK {PAGE}: landmark principal y {len(p.headings)} encabezados coherentes')