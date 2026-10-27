import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_pvp_qa', ROOT / 'scripts/build-reading-catalogue.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class ReadingPvpDate(unittest.TestCase):
    def test_impossible_price_verification_date_is_rejected(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        book = next(b for b in data['libros'] if b.get('pvp_centimos') is not None and b['estado'] != 'borrador')
        mutated = copy.deepcopy(data)
        target = next(b for b in mutated['libros'] if b['id'] == book['id'])
        target['pvp_fecha_verificacion'] = '2026-02-30'
        with self.assertRaises(mod.ValidationError):
            mod.validate(mutated, ROOT)

if __name__ == '__main__':
    unittest.main()