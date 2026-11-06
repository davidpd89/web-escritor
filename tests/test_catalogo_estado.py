"""Estado de la ingesta Amazon en la rama catalogo-estado: ida y vuelta, sin commits vacíos, sin --force."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import catalogo_estado as estado


def run(*args, cwd):
    return subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


class EstadoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.remote = base / 'remote.git'
        run('init', '--bare', '-q', str(self.remote), cwd=base)
        self.repos = []
        for name in ('a', 'b'):
            repo = base / name
            run('init', '-q', str(repo), cwd=base)
            run('remote', 'add', 'origin', str(self.remote), cwd=repo)
            self.repos.append(repo)

    def tearDown(self):
        self.tmp.cleanup()

    def use(self, repo):
        return patch.multiple(estado, ROOT=repo, WORK=repo / '.local/catalogo')

    def test_first_run_starts_empty_and_saves_then_restores_elsewhere(self):
        a, b = self.repos
        with self.use(a):
            self.assertEqual(estado.restaurar(), 0)
            work = a / '.local/catalogo'
            (work / 'revision').mkdir(parents=True)
            (work / 'semillas.json').write_text('{"cola": ["9788400000001"]}', encoding='utf-8')
            (work / 'revision/foto-2026-11-05.json').write_text('{}', encoding='utf-8')
            (work / 'revision/foto-2026-11-06.json').write_text('{"n": 1}', encoding='utf-8')
            (work / 'raw').mkdir()
            (work / 'raw/2026-11-06.jsonl').write_text('crudo', encoding='utf-8')
            first = estado.guardar('uno')
            self.assertEqual(estado.guardar('igual'), first, 'sin cambios no hay commit nuevo')
        with self.use(b):
            self.assertEqual(estado.restaurar(), 2)
            work = b / '.local/catalogo'
            self.assertEqual((work / 'semillas.json').read_text(encoding='utf-8'), '{"cola": ["9788400000001"]}')
            self.assertTrue((work / 'revision/foto-2026-11-06.json').exists(), 'solo la última foto')
            self.assertFalse((work / 'revision/foto-2026-11-05.json').exists())
            self.assertFalse((work / 'raw').exists(), 'los crudos no viajan')
            (work / 'semillas.json').write_text('{"cola": []}', encoding='utf-8')
            second = estado.guardar('dos')
        self.assertEqual(run('rev-parse', f'{second}^', cwd=b), first, 'cada guardado cuelga del anterior')
        self.assertEqual(run('rev-parse', 'refs/heads/catalogo-estado', cwd=self.remote), second)


if __name__ == '__main__':
    unittest.main()
