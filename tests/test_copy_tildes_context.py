import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('copy_tildes', ROOT / 'scripts/check-copy-tildes.py')
tildes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tildes)

class ContextTests(unittest.TestCase):
    def flagged(self, text):
        return [w for w in tildes.WORD_RE.findall(text)
                if not tildes.is_technical_use(text, w.lower())]

    def test_truncated_author_keeps_its_name(self):
        text = 'Grandes historias de la mitología griega, de Frances…'
        self.assertEqual(self.flagged(text), [])
        self.assertEqual(tildes.restore_accents(text), text)
        self.assertEqual(self.flagged('Una obra de Frances Bianchi'), [])

    def test_practica_as_a_verb_is_valid_spanish(self):
        text = 'El soporte permite consultar los pasos mientras se practica con los materiales de pintura.'
        self.assertEqual(self.flagged(text), [])
        self.assertEqual(tildes.restore_accents(text), text)

    def test_real_missing_accents_still_fail(self):
        self.assertEqual(self.flagged('Un autor frances…'), ['frances'])
        self.assertEqual(self.flagged('Nueva edicion con informacion tecnica'), ['edicion', 'informacion', 'tecnica'])
        self.assertEqual(tildes.restore_accents('Un autor frances…'), 'Un autor francés…')


class JsStringsScaleTests(unittest.TestCase):
    """21/11 (#1510): `assets/page-order.generated.js` crece con cada libro y recontar las líneas desde el principio
    en cada literal colgó la CI a los 50 min. Las líneas se cuentan una vez y la salida no cambia."""

    def old(self, src):  # la versión cuadrática, como referencia de la salida
        out = []
        for m in tildes.JS_STRING_RE.finditer(src):
            text = m.group(2)
            if len(text) < 8 or ' ' not in text or text.startswith(('http', '/', './', '../')) or '://' in text:
                continue
            line_no = src[:m.start()].count('\n') + 1
            lines = src.splitlines()
            out.append((line_no, text, lines[line_no - 1] if line_no <= len(lines) else text))
        return out

    def test_same_lines_and_context_as_before(self):
        src = ('const a = "una frase con informacion";\nconst b = "x";\n\n'
               "const c = ['otra frase larga', 'ruta/sin-espacios'];\n`plantilla con texto\nde dos lineas`;\n"
               'const d = "http://no se mira";\nconst e = "ultimo trozo de texto"')
        self.assertEqual(tildes.js_strings(src), self.old(src))
        self.assertEqual([n for n, *_ in tildes.js_strings(src)], [1, 4, 8])  # un literal partido en dos líneas no es una frase de JS

    def test_linear_in_the_size_of_the_file(self):
        import time
        src = '\n'.join(f'{{"t": "titulo del libro numero {i}", "u": "/libros/{i}/"}},' for i in range(60000))
        start = time.perf_counter()
        self.assertEqual(len(tildes.js_strings(src)), 60000)
        self.assertLess(time.perf_counter() - start, 10, 'js_strings no puede recontar el fichero en cada literal')


if __name__ == '__main__':
    unittest.main()
