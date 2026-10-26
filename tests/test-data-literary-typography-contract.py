import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/manecillas-capitulo-1-1.txt'


class LiteraryTypographyContract(unittest.TestCase):
    def test_published_fragment_typography(self):
        text = SOURCE.read_text(encoding='utf-8')
        self.assertIn('\n---\n', text, str(SOURCE))
        body = text.split('\n---\n', 1)[1]
        dialogue = [(number, line) for number, line in enumerate(body.splitlines(), 1) if line.startswith('—')]
        self.assertTrue(dialogue, f'{SOURCE}: no se reconocen diálogos con raya')
        self.assertNotIn('\ufffd', body, f'{SOURCE}: carácter de sustitución Unicode')
        for number, line in enumerate(body.splitlines(), 1):
            for character in line:
                self.assertFalse(ord(character) < 32 and character != '\t', f'{SOURCE}:{number}: control U+{ord(character):04X}')
        for number, line in dialogue:
            self.assertTrue(line[1:].strip(), f'{SOURCE}:{number}: raya de diálogo sin contenido')


if __name__ == '__main__':
    unittest.main()
