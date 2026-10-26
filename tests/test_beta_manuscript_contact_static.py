import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = 'lectores-beta/enviar-manuscrito/index.html'
SCRIPT = 'assets/email-reveal.js'

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs))

class ManuscriptContactTest(unittest.TestCase):
    def test_contact_preserves_local_mail_intent(self):
        parser = Links()
        parser.feed((ROOT / PAGE).read_text(encoding='utf-8'))
        links = [a for a in parser.links if 'Envío de manuscrito' in a.get('data-email-subject', '')]
        self.assertEqual(len(links), 1, f'{PAGE}: falta un único acceso específico para enviar manuscritos')
        link = links[0]
        self.assertIn('data-email-reveal', link, f'{PAGE}: el contacto debe utilizar revelado local')
        self.assertEqual(link.get('href'), '/prensa.html#contacto', f'{PAGE}: destino base de contacto inesperado')
        script = (ROOT / SCRIPT).read_text(encoding='utf-8')
        self.assertIn('new URLSearchParams()', script, f'{SCRIPT}: falta codificación de parámetros de correo')
        self.assertIn("params.set('subject', subject)", script, f'{SCRIPT}: el asunto del manuscrito no se conserva')
        self.assertIn('mailto:', script, f'{SCRIPT}: el contacto ya no utiliza correo local')
        self.assertIn("event.preventDefault()", script, f'{SCRIPT}: falta interceptar el enlace de revelado')
        self.assertNotIn('fetch(', script, f'{SCRIPT}: el revelado de contacto no debe transmitir datos por HTTP')
        self.assertNotIn('sendBeacon(', script, f'{SCRIPT}: el revelado de contacto no debe emitir telemetría personal')

if __name__ == '__main__':
    unittest.main()
