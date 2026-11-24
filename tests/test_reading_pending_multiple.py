"""Varios pendientes no exigen una persona (Fable R4-11, F8).

Antes: dos PR de carga abiertas abortaban cada ejecución con «Hay varias cargas pendientes» hasta que alguien
cerraba una, y varios puntos de guardado necesitaban varias noches porque una carga recuperada sin altas no
encadenaba. Ahora la más nueva sigue, las demás pasan a puntos de guardado (creados antes de cerrar la PR) y la
cadena sigue mientras queden. Repositorio git real con origin desnudo.
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

BASE = ('a', 'b', 'c', 'd', 'e', 'f')
REAL_CHECKPOINTS = refresh.checkpoints
OLD, NEW = 'automation/reading-catalogue-2026-11-15-100', 'automation/reading-catalogue-2026-11-16-200'


class MultiplePendingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Repo(self.tmp.name)
        os.environ.pop('GITHUB_RUN_ID', None)
        self.base = self.repo.git('rev-parse', 'HEAD')

    def tearDown(self):
        self.tmp.cleanup()

    def push_branch(self, name, *ids):
        """Una rama de datos sobre la base con una alta propia, como una carga o un punto de guardado."""
        repo = self.repo
        repo.git('switch', '-q', '--detach', self.base)
        repo.write({CATALOGUE: books(*BASE, *ids)})
        repo.git('commit', '-qam', name)
        repo.git('push', '-q', 'origin', 'HEAD:refs/heads/' + name)
        repo.git('switch', '-q', '--detach', self.base)

    def fake_gh(self, closed):
        numbers = {OLD: 1500, NEW: 1501}

        def gh(*args):
            if args[:2] == ('pr', 'view'):
                return json.dumps({'number': numbers[args[2]]})
            if args[:2] == ('pr', 'close'):
                # Crear antes de destruir: al cerrar, los datos ya están en un punto de guardado.
                closed.append((args[2], refresh.checkpoints(root=self.repo.work)))
                return ''
            raise AssertionError(args)
        return gh

    def test_two_open_batches_and_three_checkpoints_converge_without_a_person(self):
        repo = self.repo
        for n, book in enumerate(('g1', 'g2', 'g3'), 1):
            self.push_branch(f'{refresh.CHECKPOINT_PREFIX}2026-11-14-{n}', book)
        self.push_branch(OLD, 'viejo')
        self.push_branch(NEW, 'nuevo')

        closed = []
        with patch.object(refresh.publisher.publication, 'gh', side_effect=self.fake_gh(closed)):
            self.assertEqual(refresh.reconcile_pending([NEW, OLD], root=repo.work), NEW)
        # Solo se cierra la vieja, y cuando ya tiene su punto de guardado; su rama se conserva.
        self.assertEqual([c[0] for c in closed], ['1500'])
        saved = closed[0][1]
        self.assertEqual(len(saved), 4)
        self.assertIn(OLD, repo.git('ls-remote', '--heads', 'origin', OLD))

        # Cada ejecución publica un punto de guardado (carry + fusión) y la cadena sigue mientras quedan.
        runs, reports = 0, []
        while refresh.checkpoints(root=repo.work):
            runs += 1
            self.assertLessEqual(runs, 4, 'no converge')
            current = refresh.checkpoints(root=repo.work)[0]
            self.assertTrue(refresh.carry(current, root=repo.work))
            repo.git('add', '--all')
            repo.git('commit', '-qm', 'publica ' + current)
            repo.git('push', '-q', 'origin', 'HEAD:main')
            with patch.object(refresh, 'checkpoints', lambda root=None: REAL_CHECKPOINTS(root=repo.work)), \
                    patch.object(refresh, 'write_if_changed', lambda path, data: reports.append(data)):
                refresh.chain_report(1, consumed=current)
            refresh.drop_checkpoint(current, root=repo.work)
        self.assertEqual(runs, 4)
        self.assertEqual([r['stats']['checkpoints_restantes'] for r in reports], [3, 2, 1, 0])
        repo.git('fetch', '-q', 'origin', 'main')
        published = refresh.catalogue_ids(repo.git('show', 'origin/main:' + CATALOGUE))
        self.assertLessEqual({'g1', 'g2', 'g3', 'viejo'}, published)

    def test_recovered_or_moved_batch_still_owes_the_night_query(self):
        # 21/11 (carga 44843220015): un punto de guardado ya publicado gastó el turno con 0 altas y la noche no consultó.
        reports = []
        with patch.object(refresh, 'checkpoints', lambda root=None: []),                 patch.object(refresh, 'write_if_changed', lambda path, data: reports.append(data)):
            refresh.chain_report(0, consumed='x', recuperado_de='x', new_books=[])
            refresh.chain_report(0, trasladada_de='automation/y', new_books=[])
            refresh.chain_report(0, reanudada='automation/z')
            refresh.chain_report(3)
        self.assertEqual([r['stats']['consulta_pendiente'] for r in reports], [1, 1, 0, 0])

    def test_a_single_pending_batch_is_not_touched(self):
        with patch.object(refresh.publisher.publication, 'gh', side_effect=AssertionError):
            self.assertEqual(refresh.reconcile_pending([NEW], root=self.repo.work), NEW)

    def test_refresh_no_longer_stops_on_several_pending_batches(self):
        opened = [{'headRefName': OLD}, {'headRefName': NEW}]
        with patch.object(refresh.subprocess, 'check_output', return_value=''), \
                patch.object(refresh, 'read_json', return_value={'autopublish': True}), \
                patch.object(refresh, 'reconcile_deploy'), \
                patch.object(refresh.publisher.publication, 'gh', return_value=json.dumps(opened)), \
                patch.object(refresh, 'reconcile_pending', return_value=NEW) as reconcile, \
                patch.object(refresh.publisher, 'resume_pending', return_value='resumed') as resume, \
                patch.object(refresh, 'chain_report') as report:
            refresh.refresh(publish=True)
        reconcile.assert_called_once_with([OLD, NEW])
        resume.assert_called_once_with(NEW)
        report.assert_called_once_with(0, reanudada=NEW)


if __name__ == '__main__':
    unittest.main()
