import concurrent.futures
import importlib.util
import json
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODAY = date(2026, 10, 22)


def load(name):
    path = ROOT / 'scripts/research' / (name + '.py')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ConcurrentReviewTests(unittest.TestCase):
    def test_parallel_real_review_reports_are_complete(self):
        directory = json.loads((ROOT / 'data/editoriales.json').read_text(encoding='utf-8'))
        publishers = json.loads((ROOT / 'data/reading-publishers.json').read_text(encoding='utf-8'))
        books = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        base = ROOT / 'docs/research/gpt'
        observations = json.loads((base / 'editoriales-e4-observaciones-2026-10-22.json').read_text(encoding='utf-8'))
        hosts = json.loads((base / 'editoriales-e4-trusted-hosts-2026-10-22.json').read_text(encoding='utf-8'))
        reconcile = load('gpt_editoriales_reconcile')
        contacts = load('gpt_editoriales_contact_evidence')
        planner = load('gpt_editoriales_review_plan')

        def run(_):
            identities = reconcile.reconcile(directory, publishers, books, as_of=TODAY)
            evidence = contacts.review(observations, hosts, as_of=TODAY)
            return planner.plan(directory, identities, evidence, as_of=TODAY, max_tasks=100)

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            reports = list(pool.map(run, range(16)))
        reference = json.dumps(reports[0], ensure_ascii=False, sort_keys=True)
        self.assertGreater(reports[0]['review_tasks_total'], 0, 'Directorio real: revisión vacía')
        for index, report in enumerate(reports):
            with self.subTest(execution=index):
                self.assertEqual(json.dumps(report, ensure_ascii=False, sort_keys=True), reference, f'Ejecución {index}: informe divergente')
                self.assertEqual(report['as_of'], TODAY.isoformat())
                self.assertFalse(report['publication_enabled'])
                self.assertTrue(all(t['reason'].strip() and t['slug'] for t in report['tasks']), f'Ejecución {index}: tareas incompletas')
