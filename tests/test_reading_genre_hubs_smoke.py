"""Las páginas de género y sus RSS solo enlazan fichas publicadas que existen.

Entra en la puerta de datos de la carga por el patrón `test_*_smoke.py`. El fallo nombra los libros responsables
(los que una página de género o un feed enlaza sin ficha) para que la cuarentena los aparte y el resto siga.
"""
import json
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from contrato_libros import incumplen  # noqa: E402

SITE = 'https://davidportodiaz.com/'


def published_by_path():
    data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
    return {f"recomendaciones/libros/{b['slug']}/": b['id'] for b in data['libros'] if b['estado'] == 'publicado'}, \
        {f"recomendaciones/libros/{b['slug']}/": b['id'] for b in data['libros']}


class GenreHubsSmoke(unittest.TestCase):
    def test_hub_lists_and_feeds_only_link_existing_published_books(self):
        published, every = published_by_path()
        bad = {}
        for page in sorted((ROOT / 'recomendaciones/generos').glob('*/index.html')):
            html = page.read_text(encoding='utf-8')
            if 'noindex' in html[:400]:
                continue
            graph = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)[1])['@graph']
            items = next((n for n in graph if n['@type'] == 'ItemList'), {'itemListElement': []})['itemListElement']
            links = [i['url'].removeprefix(SITE) for i in items]
            feed = page.parent / 'feed.xml'
            if feed.exists():
                links += [i.findtext('link').removeprefix(SITE) for i in ET.parse(feed).getroot().iter('item')]
            for rel in links:
                if rel not in published or not (ROOT / rel / 'index.html').exists():
                    bad[every.get(rel, rel)] = f'{page.parent.name}: enlaza {rel} sin ficha publicada'
        incumplen('página de género con un libro sin ficha', bad)


if __name__ == '__main__':
    unittest.main()
