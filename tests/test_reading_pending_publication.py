"""A pending batch must never publish obsolete pages or discard human work."""
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('reading_pending_publication',
    Path(__file__).resolve().parents[1] / 'scripts/publish-reading-refresh.py')
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)
BRANCH = 'automation/reading-catalogue-2026-10-21-123'


class PendingPublicationTests(unittest.TestCase):
    def check_case(self, *, behind=1, bot=True, paths=None, changed=False):
        calls = []
        pr = {'number': 674, 'headRefOid': 'a' * 40, 'baseRefName': 'main',
              'state': 'OPEN', 'author': {'is_bot': bot,
                  'login': 'app/github-actions' if bot else 'davidpd89'}}

        def gh(*args):
            calls.append(args)
            if args[:2] == ('repo', 'view'):
                return 'davidpd89/web-escritor'
            if args[:2] == ('pr', 'view'):
                return json.dumps({'headRefOid': 'b' * 40} if args[-1] == 'headRefOid' and changed else pr)
            if args[0] == 'api' and '/compare/' in args[-1]:
                return json.dumps({'behind_by': behind})
            if args[0] == 'api':
                return json.dumps([[{'filename': path} for path in
                    (paths if paths is not None else ['data/reading-catalogue.json',
                        'recomendaciones/libros/prueba/index.html'])]])
            if args[:2] == ('pr', 'close'):
                return ''
            raise AssertionError(args)

        return calls, gh

    def test_current_batch_resumes_without_closing_or_regenerating(self):
        calls, gh = self.check_case(behind=0)
        with patch.object(publisher.publication, 'gh', side_effect=gh), patch.object(publisher, 'run') as run:
            self.assertTrue(publisher.resume_pending(BRANCH))
        run.assert_called_once_with(BRANCH)
        self.assertFalse(any(c[:2] == ('pr', 'close') for c in calls))

    def test_stale_generated_batch_is_preserved_and_regenerated(self):
        calls, gh = self.check_case()
        with patch.object(publisher.publication, 'gh', side_effect=gh), patch.object(publisher, 'run') as run:
            self.assertFalse(publisher.resume_pending(BRANCH))
        run.assert_not_called()
        self.assertEqual(sum(c[:2] == ('pr', 'close') for c in calls), 1)
        self.assertFalse(any('--delete-branch' in c for c in calls))

    def test_human_or_non_generated_work_is_never_closed(self):
        for options in ({'bot': False}, {'paths': ['scripts/build-reading-catalogue.py']},
                        {'paths': []}, {'changed': True}):
            with self.subTest(options=options):
                calls, gh = self.check_case(**options)
                with patch.object(publisher.publication, 'gh', side_effect=gh), patch.object(publisher, 'run') as run:
                    with self.assertRaises(ValueError):
                        publisher.resume_pending(BRANCH)
                run.assert_not_called()
                self.assertFalse(any(c[:2] == ('pr', 'close') for c in calls))

    def test_unrelated_branch_cannot_be_closed(self):
        with patch.object(publisher.publication, 'gh') as gh:
            with self.assertRaises(ValueError):
                publisher.resume_pending('research/catalogue')
        gh.assert_not_called()


if __name__ == '__main__':
    unittest.main()
