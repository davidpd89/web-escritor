import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_price_chronology_qa', ROOT / 'scripts/build-reading-catalogue.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class ReadingPriceChronology(unittest.TestCase):
    def test_price_verification_after_page_update_is_invalid(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        mutated = copy.deepcopy(data)
        target = next(b for b in mutated['libros'] if b.get('pvp_centimos') is not None and b['estado'] != 'borrador')
        target['pvp_fecha_verificacion'] = '2099-12-31'
        target['fecha_actualizacion'] = '2026-10-24'
        with self.assertRaises(mod.ValidationError):
            mod.validate(mutated, ROOT)

if __name__ == '__main__':
    unittest.main()