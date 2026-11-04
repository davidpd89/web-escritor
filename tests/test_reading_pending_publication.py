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
    def check_case(self, *, behind=1, bot=True, paths=None, changed=False, failed=False):
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
            if args[0] == 'api' and args[-1].endswith('/status'):
                return json.dumps({'statuses': [{'context': 'reflow-sitewide', 'state': 'failure' if failed else 'success'}]})
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

    def test_red_batch_is_regenerated_instead_of_retested(self):
        calls, gh = self.check_case(behind=0, failed=True)
        with patch.object(publisher.publication, 'gh', side_effect=gh), patch.object(publisher, 'run') as run:
            self.assertFalse(publisher.resume_pending(BRANCH))
        run.assert_not_called()
        close = [c for c in calls if c[:2] == ('pr', 'close')]
        self.assertEqual(len(close), 1)
        self.assertIn('reflow-sitewide', close[0][-1])

    def test_failed_publication_is_marked_on_its_commit(self):
        posted = []
        pr = {'number': 674, 'headRefOid': 'a' * 40, 'mergeStateStatus': 'CLEAN'}

        def gh(*args):
            return 'davidpd89/web-escritor' if args[:2] == ('repo', 'view') else json.dumps(pr)

        for exc, marked in ((RuntimeError('recommendations-browser-qa.yml failed'), True),
                            (publisher.publication.StaleMerge('main moved'), False),
                            (TimeoutError('CI timed out'), False)):
            with self.subTest(exc=type(exc).__name__):
                posted.clear()
                with patch.object(publisher.publication, 'gh', side_effect=gh),                         patch.object(publisher.publication, 'publish_generated', side_effect=exc),                         patch.object(publisher.publication, 'report_job', side_effect=lambda *a: posted.append(a)):
                    with self.assertRaises(type(exc)):
                        publisher.run(BRANCH)
                self.assertEqual(bool(posted), marked)

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
