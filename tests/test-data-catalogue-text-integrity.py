import json
import pathlib
import unicodedata
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/reading-catalogue.json'


class CatalogueTextIntegrity(unittest.TestCase):
    def test_active_category_text(self):
        data = json.loads(SOURCE.read_text(encoding='utf-8'))
        categories = [row for row in data['categorias'] if row.get('activa')]
        self.assertTrue(categories, f'{SOURCE}: no hay categorías activas para verificar')
        for row in categories:
            for field in ('nombre', 'descripcion'):
                value = row.get(field)
                context = f'{SOURCE}: categoría {row.get("id")}, campo {field}'
                self.assertIsInstance(value, str, context)
                self.assertTrue(value.strip(), context)
                self.assertEqual(value, value.strip(), f'{context}: espacios exteriores')
                for char in value:
                    self.assertNotEqual(char, '\ufffd', f'{context}: carácter de sustitución')
                    self.assertNotEqual(unicodedata.category(char), 'Cc', f'{context}: control U+{ord(char):04X}')
                    self.assertNotEqual(unicodedata.category(char), 'Cf', f'{context}: carácter de formato invisible U+{ord(char):04X}')


if __name__ == '__main__':
    unittest.main()
