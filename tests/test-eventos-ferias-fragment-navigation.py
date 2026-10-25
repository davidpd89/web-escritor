from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]


class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.links = []
        self.current_link = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.ids.add(attrs['id'])
        if tag == 'a':
            self.current_link = {
                'href': attrs.get('href', ''),
                'text': '',
                'line': self.getpos()[0],
            }

    def handle_data(self, data):
        if self.current_link is not None:
            self.current_link['text'] += data

    def handle_endtag(self, tag):
        if tag == 'a' and self.current_link is not None:
            self.links.append(self.current_link)
            self.current_link = None


def parse(relative_path):
    document = Document()
    document.feed((ROOT / relative_path).read_text(encoding='utf-8'))
    return document


def test_aranjuez_documentation_link():
    source = parse('eventos.html')
    destination = parse('ferias.html')

    matches = [
        link for link in source.links
        if 'Ver documentación del evento' in link['text']
    ]
    assert len(matches) == 1, (
        'eventos.html debe conservar un único enlace documental de Aranjuez'
    )

    link = matches[0]
    parsed = urlsplit(link['href'])
    assert parsed.path == '/ferias.html', (
        f"eventos.html:{link['line']}: destino incorrecto: {link['href']}"
    )
    assert parsed.fragment, (
        f"eventos.html:{link['line']}: falta el fragmento de la ficha"
    )

    fragment = unquote(parsed.fragment)
    assert fragment in destination.ids, (
        f"eventos.html:{link['line']}: {link['href']} apunta a un "
        f"fragmento inexistente en ferias.html. "
        'La ficha publicada utiliza el identificador '
        'feria-libro-aranjuez-2026.'
    )

    assert fragment == 'feria-libro-aranjuez-2026', (
        'El enlace debe identificar la ficha documental concreta de Aranjuez'
    )


if __name__ == '__main__':
    test_aranjuez_documentation_link()
    print('OK: navegación documental Eventos → Feria de Aranjuez')
