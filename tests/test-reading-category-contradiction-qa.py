import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_category_qa', ROOT / 'scripts/build-reading-catalogue.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class ReadingCategoryContradiction(unittest.TestCase):
    def test_assigned_category_cannot_be_excluded(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        mutated = copy.deepcopy(data)
        relation = next(r for r in mutated['libro_categorias'] if any(b['id'] == r['libro_id'] and b['estado'] == 'publicado' for b in mutated['libros']))
        book = next(b for b in mutated['libros'] if b['id'] == relation['libro_id'])
        book['categorias_excluidas'] = list(set(book.get('categorias_excluidas', [])) | {relation['categoria_id']})
        with self.assertRaises(mod.ValidationError):
            mod.validate(mutated, ROOT)

if __name__ == '__main__':
    unittest.main()