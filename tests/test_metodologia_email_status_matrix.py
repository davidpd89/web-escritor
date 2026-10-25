import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = json.loads((ROOT / 'data/editoriales.json').read_text(encoding='utf-8'))

class EmailStatusMatrix(unittest.TestCase):
    def check_fixture(self, status, direct, email):
        fixture = copy.deepcopy(RAW)
        record = copy.deepcopy(fixture['publishers'][0])
        record['status'] = status
        record['direct_submission'] = direct
        record['submission_email'] = email
        fixture['publishers'] = [record]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'input.json'
            source.write_text(json.dumps(fixture, ensure_ascii=False), encoding='utf-8')
            result = subprocess.run(['python3', 'scripts/build-editoriales.py', '--data', str(source), '--check', '--today', '2026-10-24'], cwd=ROOT, capture_output=True, text=True)
            return result.returncode

    def test_email_requires_open_direct_reception(self):
        for status in ['open', 'closed', 'indirect', 'award_only', 'unknown']:
            for direct in [False, True]:
                for email in [None, 'manuscritos@ejemplo.invalid']:
                    with self.subTest(status=status, direct=direct, email=email):
                        result = self.check_fixture(status, direct, email)
                        forbidden = bool(email) and (status != 'open' or not direct)
                        if forbidden:
                            self.assertNotEqual(result, 0)
                        elif status == 'open' and direct:
                            self.assertEqual(result, 0)

if __name__ == '__main__':
    unittest.main()