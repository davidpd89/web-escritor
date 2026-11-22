"""El push de la carga no puede quedarse colgado (22/11: run 44966182798, ~1 h en un `git push` sin límite).

Repositorios git reales con un origin desnudo cuyo hook `pre-receive` simula un servidor lento."""
import importlib.util
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('refresh_push', ROOT / 'scripts/refresh-reading-catalogue.py')
refresh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refresh)


def git(*args, cwd):
    return subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


class PushConLimite(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name)
        self.origin, self.work = base / 'origin.git', base / 'work'
        git('init', '--bare', '-q', str(self.origin), cwd=base)
        git('init', '-q', str(self.work), cwd=base)
        git('config', 'user.email', 'a@b.c', cwd=self.work)
        git('config', 'user.name', 't', cwd=self.work)
        (self.work / 'f.txt').write_text('x')
        git('add', '.', cwd=self.work)
        git('commit', '-qm', 'uno', cwd=self.work)
        git('remote', 'add', 'origin', self.origin.as_posix(), cwd=self.work)
        self.hook = self.origin / 'hooks' / 'pre-receive'

    def hook_sh(self, body):
        self.hook.write_text('#!/bin/sh\n' + body + '\n')
        self.hook.chmod(self.hook.stat().st_mode | stat.S_IEXEC)

    def has_branch(self):
        return bool(git('branch', '--list', 'ramita', cwd=self.origin))

    def test_push_normal(self):
        refresh.push('HEAD:refs/heads/ramita', root=self.work, timeout=60)
        self.assertTrue(self.has_branch())

    @unittest.skipIf(os.name == 'nt', 'hook de shell')
    def test_push_parado_se_corta_y_falla_con_mensaje(self):
        self.hook_sh('sleep 30')
        with patch.object(refresh.time, 'sleep'):
            with self.assertRaisesRegex(RuntimeError, 'falló tras 2 intentos'):
                refresh.push('HEAD:refs/heads/ramita', root=self.work, timeout=2, attempts=2)
        self.assertFalse(self.has_branch())

    @unittest.skipIf(os.name == 'nt', 'hook de shell')
    def test_un_intento_lento_se_repite_y_el_segundo_llega(self):
        marca = self.origin / 'ya'
        self.hook_sh(f'if [ ! -e "{marca.as_posix()}" ]; then touch "{marca.as_posix()}"; sleep 30; fi')
        with patch.object(refresh.time, 'sleep'):
            refresh.push('HEAD:refs/heads/ramita', root=self.work, timeout=2, attempts=3)
        self.assertTrue(self.has_branch())


if __name__ == '__main__':
    unittest.main()
