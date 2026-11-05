"""El espacio ante puntuación en sinopsis se corrige al escribir el catálogo, no tumba la ronda de ingesta."""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reading_intake_core import tidy_prose  # noqa: E402

GATE = re.compile(r'\w [,.;:)]')  # criterio de test_published_synopses_have_no_space_before_punctuation


class ProseTidy(unittest.TestCase):
    def test_removes_space_before_punctuation(self):
        self.assertEqual(tidy_prose('Una vida , un amor ; y un final .'), 'Una vida, un amor; y un final.')
        self.assertEqual(tidy_prose('(texto ) y ¿quién ?'), '(texto) y ¿quién?')
        self.assertEqual(tidy_prose('Pausa ... y sigue'), 'Pausa... y sigue')

    def test_output_always_passes_the_catalogue_gate(self):
        for text in ('vida .', 'a :b', 'fin .»', 'uno , dos', 'x ) y'):
            self.assertIsNone(GATE.search(tidy_prose(text)), text)

    def test_leaves_other_text_alone(self):
        self.assertEqual(tidy_prose('— Hola, mundo. ¿Qué tal?'), '— Hola, mundo. ¿Qué tal?')
        self.assertIsNone(tidy_prose(None))


if __name__ == '__main__':
    unittest.main()
