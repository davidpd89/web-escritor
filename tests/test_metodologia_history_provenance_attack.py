import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'data/editoriales.json').read_text(encoding='utf-8'))

class HistoricalProvenanceTest(unittest.TestCase):
    def test_existing_history_has_declared_sources(self):
        for record in DATA['publishers']:
            if not record.get('publish'):
                continue
            known = {s['url'] for s in record['sources']}
            known.update([record['submission_url'], record['website_url']])
            known.update(record.get('unavailable_urls', []))
            for event in record['history']:
                with self.subTest(slug=record['slug'], date=event['date']):
                    self.assertIn(event['source_url'], known)

    def test_foreign_historical_source_is_rejected(self):
        fixture = copy.deepcopy(DATA)
        record = copy.deepcopy(fixture['publishers'][0])
        record['history'][0]['source_url'] = 'https://fuente-ajena.invalid/verificacion-falsa'
        fixture['publishers'] = [record]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'editoriales.json'
            source.write_text(json.dumps(fixture, ensure_ascii=False), encoding='utf-8')
            result = subprocess.run(['python3', 'scripts/build-editoriales.py', '--data', str(source), '--check', '--today', '2026-10-24'], cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0, 'El builder ha aceptado una prueba histórica sin procedencia declarada')

if __name__ == '__main__':
    unittest.main()