from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def visible_text(path):
    html = (ROOT / path).read_text(encoding='utf-8')
    html = re.sub(r'<script\b[^>]*>[\s\S]*?</script>', ' ', html, flags=re.I)
    html = re.sub(r'<style\b[^>]*>[\s\S]*?</style>', ' ', html, flags=re.I)
    html = re.sub(r'<[^>]+>', ' ', html)
    return re.sub(r'\s+', ' ', html.replace('–', '-').replace('—', '-'))


class PressClaims(unittest.TestCase):
    def test_duracion_de_presentaciones(self):
        start = visible_text('empieza-aqui/index.html')
        press = visible_text('prensa.html')
        self.assertIn('45-60 minutos', start)
        self.assertIn('45-60 minutos', press)

    def test_plazo_de_respuesta_documentado(self):
        start = visible_text('empieza-aqui/index.html')
        press = visible_text('prensa.html')
        self.assertIn('respuesta en 48 horas', start.lower())
        self.assertRegex(press.lower(), r'(respuesta|responder|contacto)[^.]{0,150}48 horas|48 horas[^.]{0,150}(respuesta|responder|contacto)')


if __name__ == '__main__':
    unittest.main()
