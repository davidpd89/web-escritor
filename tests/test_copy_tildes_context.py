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

if __name__ == '__main__':
    unittest.main()
