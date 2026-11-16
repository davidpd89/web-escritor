"""Reconciliar al empezar y crear antes de destruir (Fable R4-6, F3).

Puntos de muerte de la carga nocturna:
- muere entre fusionar y desplegar: una fusión con GITHUB_TOKEN no dispara Pages, así que main se quedaba sin
  publicar hasta otro push; ahora la siguiente ejecución lo despliega al empezar;
- `carry` lanza (procedencia ausente, blob que falta): cada noche moría en el mismo punto de guardado o en la misma
  PR; ahora los datos pasan a `reading-atascado-*` (o la PR se cierra conservando su rama), queda una issue y la
  noche sigue.
Repositorio git real con origin desnudo para lo que toca ramas.
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_reading_branch_retry import CATALOGUE, Repo, books, refresh  # noqa: E402

SAVED = refresh.CHECKPOINT_PREFIX + '2026-11-16-1'
PENDING = 'automation/reading-catalogue-2026-11-16-300'


class Reached(Exception):
    """La ejecución llegó a la consulta nueva: la noche no se paró."""


def deploy_gh(runs, calls):
    def gh(*args):
        calls.append(args)
        if args[:2] == ('repo', 'view'):
            return 'dueño/web\n'
        if args[0] == 'api':
            return json.dumps({'workflow_runs': runs})
        if args[:2] == ('workflow', 'run'):
            return ''
        raise AssertionError(args)
    return gh


class ReconcileDeployTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Repo(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def dispatched(self, runs):
        calls = []
        with patch.object(refresh.publisher.publication, 'gh', side_effect=deploy_gh(runs, calls)):
            result = refresh.reconcile_deploy(root=self.repo.work)
        sha = self.repo.git('rev-parse', 'origin/main')
        self.assertIn(f'head_sha={sha}', [a for a in calls if a[0] == 'api'][0][1])
        self.assertEqual(result, ('workflow', 'run', 'deploy-pages.yml', '--ref', 'main') in calls)
        return result

    def test_death_between_merge_and_deploy_is_deployed_on_the_next_run(self):
        self.assertTrue(self.dispatched([]))

    def test_a_failed_or_cancelled_deploy_of_main_is_retried(self):
        self.assertTrue(self.dispatched([{'status': 'completed', 'conclusion': 'failure'},
                                         {'status': 'completed', 'conclusion': 'cancelled'}]))

    def test_a_green_or_running_deploy_is_left_alone(self):
        self.assertFalse(self.dispatched([{'status': 'completed', 'conclusion': 'success'}]))
        self.assertFalse(self.dispatched([{'status': 'in_progress', 'conclusion': None}]))

    def test_refresh_reconciles_before_anything_else(self):
        with patch.object(refresh.subprocess, 'check_output', return_value=''), \
                patch.object(refresh, 'read_json', return_value={'autopublish': True}), \
                patch.object(refresh, 'reconcile_deploy', side_effect=Reached) as reconcile:
            with self.assertRaises(Reached):
                refresh.refresh(publish=True)
        reconcile.assert_called_once_with()


class StuckDataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Repo(self.tmp.name)
        os.environ.pop('GITHUB_RUN_ID', None)
        repo = self.repo
        base = repo.git('rev-parse', 'HEAD')
        repo.write({CATALOGUE: books('a', 'b', 'c', 'd', 'e', 'f', 'g')})
        repo.git('commit', '-qam', 'datos')
        repo.git('push', '-q', 'origin', 'HEAD:refs/heads/' + SAVED)
        self.saved_sha = repo.git('rev-parse', 'HEAD')
        repo.git('switch', '-q', '--detach', base)

    def tearDown(self):
        self.tmp.cleanup()

    def heads(self):
        out = self.repo.git('ls-remote', '--heads', 'origin')
        return {line.split('refs/heads/', 1)[1]: line.split()[0] for line in out.splitlines()}

    def test_a_checkpoint_that_cannot_be_carried_is_kept_reported_and_skipped(self):
        repo, events = self.repo, []

        def gh(*args):
            if args[:2] == ('issue', 'create'):
                # Crear antes de destruir: cuando se abre la issue, la copia ya existe y el original sigue.
                events.append(('issue', dict(self.heads())))
                return 'https://github.com/x/y/issues/1\n'
            raise AssertionError(args)

        def failing_carry(branch, root=None):
            repo.git('fetch', '-q', 'origin', f'+refs/heads/{branch}:refs/remotes/origin/{branch}')
            (Path(repo.work) / CATALOGUE).write_text('a medias', encoding='utf-8')  # escritura a medias
            raise ValueError('La recuperación no tiene procedencia publicada: isbn-g')

        with patch.object(refresh.publisher.publication, 'gh', side_effect=gh), \
                patch.object(refresh, 'carry', side_effect=failing_carry):
            try:
                refresh.carry(SAVED, root=repo.work)
            except ValueError as exc:
                keep = refresh.report_stuck(SAVED, exc, root=repo.work)

        stuck = refresh.STUCK_PREFIX + '2026-11-16-1'
        self.assertEqual(keep, stuck)
        at_issue = events[0][1]
        self.assertEqual(at_issue[stuck], self.saved_sha)
        self.assertIn(SAVED, at_issue)
        after = self.heads()
        self.assertEqual(after[stuck], self.saved_sha)
        self.assertNotIn(SAVED, after)
        # El atascado ya no es un punto de guardado: no vuelve a tumbar la noche siguiente.
        self.assertEqual(refresh.checkpoints(root=repo.work), [])
        self.assertEqual(repo.git('status', '--porcelain'), '')

    def test_refresh_skips_a_stuck_checkpoint_and_publishes_the_next(self):
        good = refresh.CHECKPOINT_PREFIX + '2026-11-16-2'

        def carry(branch, root=None):
            if branch == SAVED:
                raise ValueError('Blob fuente no disponible')
            return ['isbn-x']

        with patch.object(refresh.subprocess, 'check_output', return_value=''), \
                patch.object(refresh, 'read_json', return_value={'autopublish': True}), \
                patch.object(refresh, 'reconcile_deploy'), \
                patch.object(refresh.publisher.publication, 'gh', return_value='[]'), \
                patch.object(refresh, 'checkpoints', return_value=[SAVED, good]), \
                patch.object(refresh, 'carry', side_effect=carry), \
                patch.object(refresh, 'report_stuck') as stuck, \
                patch.object(refresh, 'chain_report'), \
                patch.object(refresh, 'assemble', return_value='ok') as assemble:
            self.assertEqual(refresh.refresh(publish=True), 'ok')
        self.assertEqual(stuck.call_args.args[0], SAVED)
        self.assertEqual(assemble.call_args.kwargs['checkpoint'], good)

    def test_a_pending_batch_that_cannot_be_carried_is_closed_kept_and_the_night_goes_on(self):
        def gh(*args):
            if args[:2] == ('pr', 'list'):
                return json.dumps([{'headRefName': PENDING}])
            if args[:2] == ('pr', 'view'):
                return json.dumps({'number': 1600})
            raise AssertionError(args)

        with patch.object(refresh.subprocess, 'check_output', return_value=''), \
                patch.object(refresh, 'read_json', return_value={'autopublish': True}), \
                patch.object(refresh, 'reconcile_deploy'), \
                patch.object(refresh.publisher.publication, 'gh', side_effect=gh), \
                patch.object(refresh.publisher, 'resume_pending', return_value='carry'), \
                patch.object(refresh, 'carry', side_effect=ValueError('Blob fuente incompleto')), \
                patch.object(refresh, 'report_stuck') as stuck, \
                patch.object(refresh.publisher, 'close_proposal') as close, \
                patch.object(refresh, 'checkpoints', return_value=[]), \
                patch.object(refresh, 'ingest', side_effect=Reached):
            with self.assertRaises(Reached):
                refresh.refresh(publish=True)
        self.assertEqual(stuck.call_args.args[0], PENDING)
        self.assertEqual(stuck.call_args.kwargs, {'number': 1600})
        close.assert_not_called()  # la cierra report_stuck, con la causa; no el mensaje de «ya está en main»

    def test_report_stuck_closes_a_pending_proposal_without_touching_its_branch(self):
        with patch.object(refresh.publisher.publication, 'gh', return_value=''), \
                patch.object(refresh.publisher, 'close_proposal') as close, \
                patch.object(refresh, 'drop_checkpoint') as drop:
            keep = refresh.report_stuck(PENDING, ValueError('x'), number=1600, root=self.repo.work)
        self.assertEqual(keep, PENDING)
        self.assertEqual(close.call_args.args[0], 1600)
        drop.assert_not_called()


if __name__ == '__main__':
    unittest.main()
