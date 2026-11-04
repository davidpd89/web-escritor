"""Reintento tras código 75 (run 41797609876): ramas únicas, traslado sin nueva consulta y main concurrente.

Repositorios git reales con un origin desnudo: el fallo original era de git (`a branch named ... already exists`),
no de la lógica, y solo un repositorio real lo reproduce.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


publication = load('publication_retry', 'scripts/publish-radar-refresh.py')
refresh = load('refresh_catalogue_retry', 'scripts/refresh-reading-catalogue.py')
texts = load('reading_texts_retry', 'scripts/reading-texts.py')
CATALOGUE = 'data/reading-catalogue.json'


def books(*ids):
    return json.dumps({'libros': [{'id': i, 'titulo': i.upper()} for i in ids]}, indent=1) + '\n'


class Repo:
    """Clon de trabajo con un origin desnudo, como el checkout de Actions."""

    def __init__(self, tmp):
        self.origin, self.work = Path(tmp, 'origin.git'), Path(tmp, 'work')
        subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main', str(self.origin)], check=True)
        subprocess.run(['git', 'clone', '-q', '-c', 'core.autocrlf=false', str(self.origin), str(self.work)], check=True, capture_output=True)
        for key, value in (('user.name', 't'), ('user.email', 't@t'), ('core.autocrlf', 'false')):
            self.git('config', key, value)
        self.git('switch', '-q', '-c', 'main')
        self.write({CATALOGUE: books('a', 'b', 'c', 'd', 'e', 'f'), 'data/reading-intake-state.json': '{"pending": []}\n',
                    'recomendaciones/index.html': '<p>6</p>\n', 'pagefind/index.txt': 'v1\n'})
        self.commit('base')
        self.git('push', '-q', 'origin', 'main')

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.work, check=True, capture_output=True, text=True).stdout.strip()

    def write(self, files):
        for rel, content in files.items():
            path = self.work / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            (path.write_bytes if isinstance(content, bytes) else lambda c: path.write_text(c, encoding='utf-8', newline='\n'))(content)

    def commit(self, message):
        self.git('add', '--all')
        self.git('commit', '-q', '-m', message)
        return self.git('rev-parse', 'HEAD')

    def main_moves(self, files, message='otro escritor'):
        """Otro escritor fusiona en origin/main mientras esta ejecución trabaja."""
        with tempfile.TemporaryDirectory() as other:
            subprocess.run(['git', 'clone', '-q', '-c', 'core.autocrlf=false', str(self.origin), other], check=True, capture_output=True)
            run = lambda *a: subprocess.run(['git', *a], cwd=other, check=True, capture_output=True)
            for key, value in (('user.name', 'o'), ('user.email', 'o@o'), ('core.autocrlf', 'false')):
                run('config', key, value)
            for rel, content in files.items():
                path = Path(other, rel)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding='utf-8', newline='\n')
            run('add', '--all')
            run('commit', '-q', '-m', message)
            run('push', '-q', 'origin', 'HEAD:main')

    def bot_batch(self, branch):
        """PR verde de la carga: libros, pendientes, portada binaria y derivados viejos."""
        self.git('switch', '-q', '-c', branch, 'origin/main')
        self.write({CATALOGUE: books('a', 'b', 'c', 'd', 'e', 'f', 'nuevo1', 'nuevo2'),
                    'data/reading-intake-state.json': '{"pending": ["9788400000000"]}\n',
                    'assets/reading-covers/nuevo1.webp': bytes(range(256)) * 4,
                    'recomendaciones/index.html': '<p>8 con renderizador viejo</p>\n', 'pagefind/index.txt': 'v2-viejo\n'})
        self.commit('carga')
        self.git('push', '-q', 'origin', branch)
        self.git('switch', '-q', '--detach', 'origin/main')


class FreshBranchTests(unittest.TestCase):
    def test_second_attempt_same_run_and_manual_rerun_get_new_names(self):
        prefix = 'automation/reading-catalogue-2026-11-04-'
        with tempfile.TemporaryDirectory() as tmp:
            repo = Repo(tmp)
            env = {'GITHUB_RUN_ID': '41797609876', 'GITHUB_RUN_ATTEMPT': '1'}
            with patch.dict(os.environ, env):
                first = publication.fresh_branch(prefix, cwd=repo.work)
                self.assertEqual(first, prefix + '41797609876')
                repo.git('switch', '-q', '-c', first)   # intento 1: la rama local queda tras el código 75
                repo.git('push', '-q', 'origin', first)
                second = publication.fresh_branch(prefix, cwd=repo.work)
                self.assertEqual(second, prefix + '41797609876-r2')
                repo.git('switch', '-q', '-c', second)  # el `switch -c` que abortó el run ahora funciona
                repo.git('switch', '-q', '--detach', 'origin/main')
                repo.git('branch', '-q', '-D', first, second)  # checkout nuevo: solo quedan las ramas de origin
                self.assertEqual(publication.fresh_branch(prefix, cwd=repo.work), prefix + '41797609876-r2')
            with patch.dict(os.environ, {**env, 'GITHUB_RUN_ATTEMPT': '2'}):
                self.assertEqual(publication.fresh_branch(prefix, cwd=repo.work), prefix + '41797609876-a2')

    def test_no_automation_names_branches_with_the_bare_run_id(self):
        for rel in ('scripts/refresh-reading-catalogue.py', 'scripts/refresh-atlas-directory.py'):
            source = (ROOT / rel).read_text(encoding='utf-8')
            self.assertNotIn('GITHUB_RUN_ID', source, rel)
            self.assertIn('publication.fresh_branch(', source, rel)


class CarryTests(unittest.TestCase):
    BRANCH = 'automation/reading-catalogue-2026-11-04-41797609876'

    def test_green_stale_batch_moves_onto_current_main_without_its_derived_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Repo(tmp)
            repo.bot_batch(self.BRANCH)
            repo.main_moves({'pagefind/index.txt': 'v1-textos\n', 'data/reading-texts/a.json': '{}\n'})
            carried = refresh.carry(self.BRANCH, root=repo.work)
            self.assertEqual(carried, ['nuevo1', 'nuevo2'])
            self.assertEqual(repo.git('rev-parse', 'HEAD'), repo.git('rev-parse', 'origin/main'))
            read = lambda rel: (repo.work / rel).read_text(encoding='utf-8')
            self.assertIn('nuevo2', read(CATALOGUE))
            self.assertIn('9788400000000', read('data/reading-intake-state.json'))  # candidatos pendientes intactos
            self.assertEqual((repo.work / 'assets/reading-covers/nuevo1.webp').read_bytes(), bytes(range(256)) * 4)
            self.assertEqual(read('pagefind/index.txt'), 'v1-textos\n')  # el índice viejo de la PR no se arrastra
            self.assertEqual(read('recomendaciones/index.html'), '<p>6</p>\n')
            self.assertTrue((repo.work / 'data/reading-texts/a.json').exists())

    def test_conflicting_source_data_returns_none_and_leaves_main_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Repo(tmp)
            repo.bot_batch(self.BRANCH)
            repo.main_moves({CATALOGUE: books('a', 'b', 'c', 'd', 'e', 'f', 'manual')})
            self.assertIsNone(refresh.carry(self.BRANCH, root=repo.work))
            self.assertEqual(repo.git('status', '--porcelain'), '')
            self.assertEqual(repo.git('rev-parse', 'HEAD'), repo.git('rev-parse', 'origin/main'))
            self.assertIn(self.BRANCH, repo.git('ls-remote', '--heads', 'origin'))  # la rama sigue como referencia

    def test_already_merged_batch_has_nothing_to_carry(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Repo(tmp)
            repo.git('push', '-q', 'origin', 'HEAD:refs/heads/' + self.BRANCH)
            self.assertIsNone(refresh.carry(self.BRANCH, root=repo.work))


class FollowMainTests(unittest.TestCase):
    def ingest(self, repo):
        repo.git('switch', '-q', '--detach', 'origin/main')
        base = repo.git('rev-parse', 'HEAD')
        repo.write({CATALOGUE: books('a', 'b', 'c', 'd', 'e', 'f', 'nuevo1'),
                    'assets/reading-covers/nuevo1.webp': b'\x00\xffRIFF'})
        return base

    def test_fresh_ingest_follows_main_that_moved_meanwhile(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Repo(tmp)
            self.ingest(repo)
            repo.main_moves({'pagefind/index.txt': 'v1-textos\n'})
            latest = refresh.follow_main(root=repo.work)
            self.assertEqual(latest, repo.git('rev-parse', 'origin/main'))
            self.assertEqual(repo.git('rev-parse', 'HEAD'), latest)
            self.assertIn('nuevo1', (repo.work / CATALOGUE).read_text(encoding='utf-8'))
            self.assertEqual((repo.work / 'assets/reading-covers/nuevo1.webp').read_bytes(), b'\x00\xffRIFF')
            self.assertEqual((repo.work / 'pagefind/index.txt').read_text(encoding='utf-8'), 'v1-textos\n')

    def test_conflict_keeps_the_ingest_on_its_own_base(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Repo(tmp)
            base = self.ingest(repo)
            repo.main_moves({CATALOGUE: books('a', 'b', 'c', 'd', 'e', 'f', 'manual')})
            self.assertEqual(refresh.follow_main(root=repo.work), base)
            self.assertEqual(repo.git('rev-parse', 'HEAD'), base)
            self.assertIn('nuevo1', (repo.work / CATALOGUE).read_text(encoding='utf-8'))
            self.assertTrue((repo.work / 'assets/reading-covers/nuevo1.webp').exists())

    def test_unchanged_main_is_a_no_op(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Repo(tmp)
            base = self.ingest(repo)
            self.assertEqual(refresh.follow_main(root=repo.work), base)
            self.assertIn('nuevo1', (repo.work / CATALOGUE).read_text(encoding='utf-8'))


class TextsYieldTests(unittest.TestCase):
    NOW = datetime(2026, 11, 4, 12, tzinfo=timezone.utc)

    def pr(self, name, minutes):
        return {'headRefName': name, 'createdAt': (self.NOW - timedelta(minutes=minutes)).isoformat().replace('+00:00', 'Z')}

    def test_texts_wait_while_a_recent_catalogue_batch_is_in_ci(self):
        batch = 'automation/reading-catalogue-2026-11-04-41797609876-r2'
        self.assertEqual(texts.catalogue_in_ci([self.pr(batch, 30)], self.NOW), batch)

    def test_old_red_batch_or_other_texts_never_block(self):
        self.assertIsNone(texts.catalogue_in_ci([
            self.pr('automation/reading-catalogue-2026-11-01-1', 60 * 26),
            self.pr('automation/reading-catalogue-textos-2026-11-04-110000', 5),
            self.pr('automation/atlas-directory-2026-11-04-1', 5)], self.NOW))


class WorkflowRetryContractTests(unittest.TestCase):
    def test_retry_resets_to_latest_main_and_is_bounded(self):
        for rel in ('.github/workflows/reading-catalogue-sync.yml', '.github/workflows/atlas-directory-sync.yml'):
            source = (ROOT / rel).read_text(encoding='utf-8')
            self.assertRegex(source, r'for attempt in 1 2\b', rel)
            self.assertIn('-ne 75', source, rel)
            self.assertIn('switch --quiet --detach origin/main', source, rel)


if __name__ == '__main__':
    unittest.main()
