"""Punto de guardado de la carga (06/11): una prueba fallida tiró 181 libros aceptados tras 40 min de ingesta.

Los datos fuente suben a `automation/reading-datos-*` antes de construir páginas y de las pruebas; la siguiente
ejecución los recupera con `carry`, sin consultar las fuentes. Repositorio git real con origin desnudo.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_reading_branch_retry import CATALOGUE, Repo, books, refresh  # noqa: E402


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Repo(self.tmp.name)
        os.environ.pop('GITHUB_RUN_ID', None)

    def tearDown(self):
        self.tmp.cleanup()

    def test_saved_data_survives_a_failed_run_and_is_carried_without_querying(self):
        repo = self.repo
        head = repo.git('rev-parse', 'HEAD')
        repo.write({CATALOGUE: books('a', 'b', 'c', 'd', 'e', 'f', 'nuevo1', 'nuevo2'),
                    'recomendaciones/libros/nuevo1/index.html': '<p>generada</p>\n'})
        branch = refresh.save_checkpoint('2026-11-06', root=repo.work)
        self.assertTrue(branch.startswith(refresh.CHECKPOINT_PREFIX + '2026-11-06-'))
        # Ni HEAD ni el índice real cambian; el trabajo sigue tal cual para construir la PR.
        self.assertEqual(repo.git('rev-parse', 'HEAD'), head)
        self.assertEqual(repo.git('diff', '--cached', '--name-only'), '')
        self.assertIn(CATALOGUE, repo.git('diff', '--name-only'))
        self.assertNotIn('checkpoint-index', repo.git('status', '--porcelain', '--untracked-files=all'))
        # Solo datos fuente: las páginas se regeneran siempre con el código actual.
        repo.git('fetch', '-q', 'origin', branch)
        self.assertEqual(repo.git('show', '--name-only', '--format=', 'FETCH_HEAD').split(), [CATALOGUE])

        # La ejecución falla; la siguiente arranca limpia sobre main, que entretanto avanzó en otra ruta.
        repo.git('reset', '-q', '--hard')
        repo.git('clean', '-qfd')
        repo.main_moves({'otro.txt': 'x\n'})
        self.assertEqual(refresh.checkpoints(root=repo.work), [branch])
        self.assertEqual(refresh.carry(branch, root=repo.work), ['nuevo1', 'nuevo2'])
        self.assertTrue((repo.work / 'otro.txt').exists())
        refresh.drop_checkpoint(branch, root=repo.work)
        self.assertEqual(refresh.checkpoints(root=repo.work), [])

    def test_nothing_consulted_leaves_no_branch(self):
        self.assertIsNone(self.repo.git('status', '--porcelain') or refresh.save_checkpoint('2026-11-06', root=self.repo.work))
        self.assertEqual(refresh.checkpoints(root=self.repo.work), [])


if __name__ == '__main__':
    unittest.main()
