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
    BOT_EMAIL = '41898282+github-actions[bot]@users.noreply.github.com'

    def check_case(self, *, behind=1, bot=True, paths=None, changed=False, failed=False, commit_email=None,
                   commits=None):
        calls = []
        # El login del autor de la PR ya no decide nada (lo fija el token que abre la PR); lo que manda es quién
        # firma los commits. Por defecto los firma la carga aunque la abriera una credencial de usuario.
        commit_email = commit_email or self.BOT_EMAIL
        # Un commit de contenido normal (un solo padre). update-branch añadiría otro con dos padres (merge).
        commits = commits if commits is not None else [{'commit': {'author': {'email': commit_email}},
                                                        'parents': [{'sha': 'p0'}]}]
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
            if args[0] == 'api' and '/commits' in args[-1]:
                return json.dumps([commits])
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
            self.assertEqual(publisher.resume_pending(BRANCH), 'resumed')
        run.assert_called_once_with(BRANCH)
        self.assertFalse(any(c[:2] == ('pr', 'close') for c in calls))

    def test_stale_green_batch_is_carried_and_stays_open_until_replaced(self):
        # Run 41797609876: closing first and querying every source again lost the 100-book batch on a collision.
        calls, gh = self.check_case()
        with patch.object(publisher.publication, 'gh', side_effect=gh), patch.object(publisher, 'run') as run:
            self.assertEqual(publisher.resume_pending(BRANCH), 'carry')
        run.assert_not_called()
        self.assertFalse(any(c[:2] == ('pr', 'close') for c in calls))

    def test_red_batch_is_regenerated_instead_of_retested(self):
        calls, gh = self.check_case(behind=0, failed=True)
        with patch.object(publisher.publication, 'gh', side_effect=gh), patch.object(publisher, 'run') as run:
            self.assertEqual(publisher.resume_pending(BRANCH), 'regenerate')
        run.assert_not_called()
        close = [c for c in calls if c[:2] == ('pr', 'close')]
        self.assertEqual(len(close), 1)
        self.assertFalse(any('--delete-branch' in c for c in calls))
        self.assertIn('reflow-sitewide', close[0][-1])

    def test_red_batch_behind_main_keeps_its_data_for_the_new_code(self):
        # 06/11: a test fixed in main afterwards must not cost the 181 accepted books of the red batch.
        calls, gh = self.check_case(behind=2, failed=True)
        with patch.object(publisher.publication, 'gh', side_effect=gh), patch.object(publisher, 'run') as run:
            self.assertEqual(publisher.resume_pending(BRANCH), 'carry')
        run.assert_not_called()
        self.assertFalse(any(c[:2] == ('pr', 'close') for c in calls))

    def test_batch_opened_under_a_user_token_is_still_the_bot_work(self):
        # Run 42945302882: una publicación lanzada en local abrió la propuesta generada bajo el login de usuario.
        # El autor de la PR no es github-actions, pero sus commits sí: se traslada, no se encalla cada noche.
        calls, gh = self.check_case(behind=1, bot=False)
        with patch.object(publisher.publication, 'gh', side_effect=gh), patch.object(publisher, 'run') as run:
            self.assertEqual(publisher.resume_pending(BRANCH), 'carry')
        run.assert_not_called()
        self.assertFalse(any(c[:2] == ('pr', 'close') for c in calls))

    def test_github_update_branch_merge_commit_is_not_human_work(self):
        # Run 42958539544: una propuesta del bot quedó BEHIND y run() llamó a update-branch; GitHub añadió un
        # merge «Merge branch 'main'…» firmado por su cuenta, no por bot_identity. Exigir que TODOS los commits
        # fueran del bot encallaba la carga cada noche. Ese merge (dos padres) es maquinaria: se traslada (carry).
        merge = {'commit': {'author': {'email': 'noreply@github.com'}}, 'parents': [{'sha': 'p1'}, {'sha': 'p2'}]}
        bot_commit = {'commit': {'author': {'email': self.BOT_EMAIL}}, 'parents': [{'sha': 'p0'}]}
        calls, gh = self.check_case(behind=1, commits=[bot_commit, merge])
        with patch.object(publisher.publication, 'gh', side_effect=gh), patch.object(publisher, 'run') as run:
            self.assertEqual(publisher.resume_pending(BRANCH), 'carry')
        run.assert_not_called()
        self.assertFalse(any(c[:2] == ('pr', 'close') for c in calls))

    def test_human_commit_alongside_a_merge_is_still_rejected(self):
        # Un merge de update-branch no blanquea un commit humano que sí aporta cambios (un solo padre): sigue
        # rechazándose para no cerrar ni regenerar trabajo de una persona.
        merge = {'commit': {'author': {'email': 'noreply@github.com'}}, 'parents': [{'sha': 'p1'}, {'sha': 'p2'}]}
        human = {'commit': {'author': {'email': 'davidpd89@users.noreply.github.com'}}, 'parents': [{'sha': 'p0'}]}
        calls, gh = self.check_case(behind=1, commits=[human, merge])
        with patch.object(publisher.publication, 'gh', side_effect=gh), patch.object(publisher, 'run') as run:
            with self.assertRaises(ValueError):
                publisher.resume_pending(BRANCH)
        run.assert_not_called()
        self.assertFalse(any(c[:2] == ('pr', 'close') for c in calls))

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
        # Un commit firmado por una persona (no por la carga) nunca se cierra ni se regenera, aunque la rama
        # tenga nombre de automatización; tampoco cambios fuera de la política de artefactos generados.
        for options in ({'commit_email': 'davidpd89@users.noreply.github.com'},
                        {'paths': ['scripts/build-reading-catalogue.py']},
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
