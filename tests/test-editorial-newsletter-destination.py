import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'assets/newsletter-general.js'


class NewsletterDestinationContract(unittest.TestCase):
    def test_subscription_destination_and_transport(self):
        source = SCRIPT.read_text(encoding='utf-8')
        urls = re.findall(r'https?://[^\s\"\'`]+', source)
        destinations = [url.rstrip(');,') for url in urls]
        self.assertTrue(destinations, 'assets/newsletter-general.js: no se encuentra destino HTTPS')
        for url in destinations:
            self.assertTrue(
                url in ('https://subscribe.davidpd89.workers.dev', 'https://subscribe.davidpd89.workers.dev/'),
                f'assets/newsletter-general.js: origen externo no autorizado: {url}',
            )
        self.assertRegex(source, r'\bfetch\s*\(', 'assets/newsletter-general.js: falta transporte de suscripción')
        self.assertNotRegex(source, r'\bsendBeacon\s*\(', 'assets/newsletter-general.js: envío paralelo mediante sendBeacon')
        self.assertNotRegex(source, r'\bnew\s+XMLHttpRequest\b', 'assets/newsletter-general.js: transporte alternativo no revisado')

    def test_editorial_pages_load_local_module(self):
        for path in ('fragmento/index.html', 'cuaderno/index.html'):
            with self.subTest(page=path):
                html = (ROOT / path).read_text(encoding='utf-8')
                scripts = re.findall(r'<script\b[^>]*\bsrc=[\"\']([^\"\']+)', html, re.I)
                matching = [s for s in scripts if s.split('?')[0] == '/assets/newsletter-general.js']
                self.assertEqual(len(matching), 1, f'{path}: módulo de suscripción ausente o duplicado')


if __name__ == '__main__':
    unittest.main()
