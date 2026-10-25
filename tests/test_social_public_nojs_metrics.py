"""Regresión: disponibilidad de las métricas públicas sin JavaScript.

El HTML inicial muestra seis veces 'Dato no disponible', aunque el
artefacto JSON publicado contiene mediciones vigentes.

Causa: redes-sociales/index.html, elementos [data-role=count],
y redes-sociales/panel.js, carga exclusiva mediante fetch(DATA_URL).
"""

from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'redes-sociales/index.html'
DATA = ROOT / 'redes-sociales/social-metrics.json'


class SocialHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.current_network = None
        self.current_role = None
        self.counts = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'li' and attrs.get('data-network'):
            self.current_network = attrs['data-network']
        if self.current_network and attrs.get('data-role') == 'count':
            self.current_role = 'count'
            self.counts.setdefault(self.current_network, '')

    def handle_data(self, data):
        if self.current_network and self.current_role == 'count':
            self.counts[self.current_network] += data

    def handle_endtag(self, tag):
        if tag == 'p' and self.current_role:
            self.current_role = None
        if tag == 'li':
            self.current_network = None
            self.current_role = None


class PublicSocialBaselineTests(unittest.TestCase):
    def test_published_fresh_metrics_have_non_js_representation(self):
        snapshot = json.loads(DATA.read_text(encoding='utf-8'))
        generated = datetime.fromisoformat(
            snapshot['generated_at'].replace('Z', '+00:00')
        )
        self.assertEqual(snapshot['schema_version'], 1)

        parser = SocialHTMLParser()
        parser.feed(PAGE.read_text(encoding='utf-8'))

        eligible = []
        for network in snapshot['networks']:
            expires = datetime.fromisoformat(
                network['valid_until'].replace('Z', '+00:00')
            )
            if network['status'] == 'ok' and expires > generated:
                eligible.append(network)

        self.assertTrue(eligible, 'La prueba requiere métricas publicadas vigentes')
        self.assertEqual(len(parser.counts), 6)

        for network in eligible:
            with self.subTest(network=network['id']):
                visible = parser.counts[network['id']].strip()
                self.assertNotEqual(
                    visible, 'Dato no disponible',
                    'El HTML declara indisponible una métrica publicada; '
                    'sin JavaScript no existe otro mecanismo para consultarla.'
                )
                digits = ''.join(ch for ch in visible if ch.isdigit())
                self.assertEqual(
                    digits, str(network['followers']),
                    'La representación inicial debe corresponder al dato publicado.'
                )


if __name__ == '__main__':
    unittest.main()
