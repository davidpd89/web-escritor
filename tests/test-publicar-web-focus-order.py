from html.parser import HTMLParser
from pathlib import Path

PAGE = Path(__file__).resolve().parents[1] / 'publicar-web/index.html'

class FocusParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_main = False
        self.depth = 0
        self.controls = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'main':
            self.in_main = True
            self.depth = 1
        elif self.in_main and tag not in ('meta', 'link', 'img', 'input', 'br', 'hr'):
            self.depth += 1
        if tag in ('a', 'button', 'input', 'select', 'textarea'):
            self.controls.append((tag, a, self.in_main))

    def handle_endtag(self, tag):
        if self.in_main:
            self.depth -= 1
            if self.depth == 0:
                self.in_main = False

p = FocusParser()
p.feed(PAGE.read_text(encoding='utf-8'))
assert p.controls, f'{PAGE}: no hay controles navegables'
for index, (tag, attrs, inside) in enumerate(p.controls, 1):
    assert inside, f'{PAGE}: control {index} ({tag}) fuera de main'
    assert attrs.get('tabindex') is None or int(attrs['tabindex']) == 0, f'{PAGE}: control {index} altera el orden natural de foco'
    assert 'hidden' not in attrs, f'{PAGE}: control {index} oculto en la secuencia'
    assert attrs.get('aria-hidden') != 'true', f'{PAGE}: control {index} oculto al lector de pantalla'
    assert 'inert' not in attrs, f'{PAGE}: control {index} inerte'
print(f'OK {PAGE}: {len(p.controls)} controles en orden documental natural')