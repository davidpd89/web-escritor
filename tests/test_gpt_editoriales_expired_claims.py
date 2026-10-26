import importlib.util
import json
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODAY = date(2026, 10, 22)


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts/research' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ExpiredClaimsTests(unittest.TestCase):
    def test_real_expired_evidence_cannot_confirm_status(self):
        root = ROOT / 'docs/research/gpt'
        observations = json.loads((root / 'editoriales-e4-observaciones-2026-10-22.json').read_text(encoding='utf-8'))
        hosts = json.loads((root / 'editoriales-e4-trusted-hosts-2026-10-22.json').read_text(encoding='utf-8'))
        report = load('gpt_editoriales_contact_evidence').review(observations, hosts, as_of=TODAY)
        self.assertEqual(report['as_of'], TODAY.isoformat())
        for publisher in report['publishers']:
            slug = publisher['slug']
            status = publisher['proposed_manuscript_status']
            sources = publisher.get('submission_status_candidates', [])
            if status in ('open', 'closed'):
                valid = [s for s in sources if s.get('expired') is False and s.get('scope') == 'publisher_specific' and s.get('proposed_status') == status]
                self.assertTrue(valid, f'{slug}: estado {status} sin prueba oficial vigente')
            if sources and all(s.get('expired') is True for s in sources):
                self.assertNotIn(status, ('open', 'closed'), f'{slug}: evidencia caducada presentada como estado confirmado')
