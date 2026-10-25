import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class ManecillasTriggerParity(unittest.TestCase):
    def test_executed_scripts_trigger_workflow(self):
        text = (ROOT / '.github/workflows/content-parity-manecillas.yml').read_text(encoding='utf-8')
        scripts = set(re.findall(r'\bnode\s+(qa/[A-Za-z0-9_.-]+\.mjs)', text))
        self.assertTrue(scripts)
        trigger = text.split('jobs:', 1)[0]
        for script in sorted(scripts):
            with self.subTest(script=script):
                self.assertIn("'" + script + "'", trigger, f'{script} no activa el workflow')

if __name__ == '__main__':
    unittest.main()