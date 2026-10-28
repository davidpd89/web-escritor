from html.parser import HTMLParser
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
FEED_URL = 'https://davidportodiaz.com/cuaderno/feed.xml'
EXPECTED_TITLE = 'Cuaderno del autor — David Porto Díaz'
EXPECTED_CANONICAL = 'https://davidportodiaz.com/'
EXPECTED_ROBOTS = 'index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1'


class HeadParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_head = False
        self.links = []
        self.metas = []

    def handle_starttag(self, tag, attrs):
        if tag == 'head':
            self.in_head = True
        elif self.in_head and tag == 'link':
            self.links.append(dict(attrs))
        elif self.in_head and tag == 'meta':
            self.metas.append(dict(attrs))

    def handle_endtag(self, tag):
        if tag == 'head':
            self.in_head = False


def read_head(path):
    parser = HeadParser()
    parser.feed(path.read_text(encoding='utf-8'))
    parser.close()
    return parser


def rss_links(head):
    return [
        link for link in head.links
        if 'alternate' in link.get('rel', '').lower().split()
        and link.get('type', '').lower() == 'application/rss+xml'
    ]


def test_home_rss_autodiscovery():
    home = read_head(ROOT / 'index.html')
    cuaderno = read_head(ROOT / 'cuaderno' / 'index.html')

    original_rss = rss_links(cuaderno)
    assert len(original_rss) == 1, 'El Cuaderno debe tener una declaración RSS única'
    assert original_rss[0].get('href') == FEED_URL, 'La URL RSS del Cuaderno no coincide con la aprobada'
    assert original_rss[0].get('title') == EXPECTED_TITLE, 'El título RSS del Cuaderno no coincide con el aprobado'

    home_rss = rss_links(home)
    assert len(home_rss) == 1, 'La portada debe declarar exactamente un RSS alternate dentro del head'
    assert home_rss[0].get('href') == original_rss[0]['href'], 'La portada debe reutilizar exactamente la URL RSS del Cuaderno'
    assert home_rss[0].get('title') == original_rss[0]['title'], 'La portada debe reutilizar exactamente el título RSS del Cuaderno'

    feed_path = ROOT / 'cuaderno' / 'feed.xml'
    assert feed_path.is_file(), 'No existe cuaderno/feed.xml'
    feed = ET.parse(feed_path).getroot()
    assert feed.tag == 'rss', 'El documento de destino debe tener una raíz rss'
    assert feed.get('version') == '2.0', 'El feed debe utilizar RSS 2.0'
    assert feed.find('channel') is not None, 'El feed debe contener channel'
    assert len(feed.findall('./channel/item')) >= 1, 'El feed debe contener al menos un item'

    canonicals = [link for link in home.links if 'canonical' in link.get('rel', '').lower().split()]
    assert len(canonicals) == 1, 'La portada debe conservar un único canonical'
    assert canonicals[0].get('href') == EXPECTED_CANONICAL, 'El canonical original de la portada ha cambiado'

    robots = [meta for meta in home.metas if meta.get('name', '').lower() == 'robots']
    assert len(robots) == 1, 'La portada debe conservar una única etiqueta meta robots'
    assert robots[0].get('content') == EXPECTED_ROBOTS, 'Las directivas robots originales de la portada han cambiado'


if __name__ == '__main__':
    test_home_rss_autodiscovery()
    print('MW-0030: aceptación correcta')
