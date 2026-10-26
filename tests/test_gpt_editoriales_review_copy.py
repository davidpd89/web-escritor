import importlib.util
import json
import re
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


class ReviewCopyTests(unittest.TestCase):
    def test_real_review_queue_contains_actionable_explanations(self):
        directory = json.loads((ROOT / 'data/editoriales.json').read_text(encoding='utf-8'))
        publishers = json.loads((ROOT / 'data/reading-publishers.json').read_text(encoding='utf-8'))
        books = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        base = ROOT / 'docs/research/gpt'
        observations = json.loads((base / 'editoriales-e4-observaciones-2026-10-22.json').read_text(encoding='utf-8'))
        hosts = json.loads((base / 'editoriales-e4-trusted-hosts-2026-10-22.json').read_text(encoding='utf-8'))
        identities = load('gpt_editoriales_reconcile').reconcile(directory, publishers, books, as_of=TODAY)
        evidence = load('gpt_editoriales_contact_evidence').review(observations, hosts, as_of=TODAY)
        report = load('gpt_editoriales_review_plan').plan(directory, identities, evidence, as_of=TODAY, max_tasks=100)
        self.assertTrue(report['tasks'], 'Directorio: ninguna tarea revisada')
        for task in report['tasks']:
            slug = task['slug']
            reason = task['reason']
            self.assertIsInstance(reason, str, f'{slug}: motivo no textual')
            self.assertGreaterEqual(len(reason.strip()), 20, f'{slug}: motivo insuficiente: {reason!r}')
            self.assertFalse(re.search(r'\b(?:TODO|TBD|FIXME|lorem ipsum)\b', reason, re.I), f'{slug}: texto provisional: {reason}')
            self.assertEqual(reason, reason.strip(), f'{slug}: motivo con espacios residuales')
            self.assertTrue(task['requires_human_review'], f'{slug}: falta revisión humana')
