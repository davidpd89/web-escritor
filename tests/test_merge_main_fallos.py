"""scripts/merge-main.py: un merge que git rechaza sin conflictos no se da por bueno, y las rutas con espacios
se resuelven enteras (#1312, Codex y CodeRabbit)."""
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('merge_main', ROOT / 'scripts/merge-main.py')
merge_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(merge_main)


def git(cwd, *args):
    return subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True, text=True,
                          encoding='utf-8').stdout.strip()


class MergeMain(unittest.TestCase):
    def repos(self, tmp):
        origen, repo = Path(tmp, 'origen.git'), Path(tmp, 'repo')
        git(tmp, 'init', '-q', '--bare', '-b', 'main', str(origen))
        git(tmp, 'clone', '-q', str(origen), str(repo))
        for cwd in (repo,):
            git(cwd, 'config', 'user.email', 'qa@example.invalid'); git(cwd, 'config', 'user.name', 'qa')
        (repo / 'recomendaciones/a b').mkdir(parents=True)
        (repo / 'recomendaciones/a b/index.html').write_text('base\n', encoding='utf-8')
        (repo / 'README').write_text('x\n', encoding='utf-8')
        git(repo, 'add', '-A'); git(repo, 'commit', '-qm', 'base'); git(repo, 'push', '-q', 'origin', 'HEAD:main')
        git(repo, 'checkout', '-qb', 'rama')
        return origen, repo

    def en_main(self, origen, tmp, cambios):
        otro = Path(tmp, 'otro')
        git(tmp, 'clone', '-q', str(origen), str(otro))
        git(otro, 'config', 'user.email', 'qa@example.invalid'); git(otro, 'config', 'user.name', 'qa')
        for ruta, texto in cambios.items():
            (otro / ruta).parent.mkdir(parents=True, exist_ok=True)
            (otro / ruta).write_text(texto, encoding='utf-8')
        git(otro, 'add', '-A'); git(otro, 'commit', '-qm', 'main avanza'); git(otro, 'push', '-q', 'origin', 'HEAD:main')

    def run_main(self, repo):
        with patch.object(merge_main, 'ROOT', repo), \
             patch.object(merge_main.materializar, 'construir'), \
             patch.object(merge_main.materializar, 'comprobar'):
            merge_main.main()

    def test_merge_rechazado_sin_conflictos_no_sigue(self):
        with tempfile.TemporaryDirectory() as tmp:
            origen, repo = self.repos(tmp)
            self.en_main(origen, tmp, {'nuevo.txt': 'de main\n'})
            (repo / 'nuevo.txt').write_text('local sin seguimiento\n', encoding='utf-8')
            with self.assertRaises(SystemExit) as salida:
                self.run_main(repo)
            self.assertIn('sin conflictos', str(salida.exception))
            self.assertNotEqual(subprocess.run(['git', 'merge-base', '--is-ancestor', 'origin/main', 'HEAD'],
                                               cwd=repo).returncode, 0)

    def test_conflicto_en_ficha_con_espacio_se_resuelve_entero(self):
        with tempfile.TemporaryDirectory() as tmp:
            origen, repo = self.repos(tmp)
            (repo / 'recomendaciones/a b/index.html').write_text('rama\n', encoding='utf-8')
            git(repo, 'commit', '-qam', 'rama toca la ficha')
            self.en_main(origen, tmp, {'recomendaciones/a b/index.html': 'main\n'})
            self.run_main(repo)
            self.assertEqual(git(repo, 'merge-base', '--is-ancestor', 'origin/main', 'HEAD'), '')
            self.assertEqual((repo / 'recomendaciones/a b/index.html').read_text(encoding='utf-8'), 'main\n')


if __name__ == '__main__':
    unittest.main()
