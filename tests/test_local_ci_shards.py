import importlib.util
import importlib.util as _iu
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('local_ci', ROOT / 'scripts' / 'local-ci.py')
local_ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(local_ci)


class Lotes(unittest.TestCase):
    @unittest.skipUnless(_iu.find_spec('yaml'), 'sin PyYAML no se leen los workflows')
    def test_la_suite_completa_se_reparte_en_lotes(self):
        commands = [c for c, _, _ in local_ci.collect(set(), True)]
        self.assertNotIn(local_ci.SUITE, commands)
        lotes = [c for c in commands if '--unittest-shard' in c]
        self.assertEqual(len(lotes), local_ci.SHARDS)

    def test_los_lotes_cubren_cada_fichero_una_vez(self):
        files = sorted(p.name for p in (ROOT / 'tests').glob('test_*.py'))
        repartidos = [f for i in range(local_ci.SHARDS) for f in files[i::local_ci.SHARDS]]
        self.assertEqual(sorted(repartidos), files)




class ScopedTest(unittest.TestCase):
    ci = local_ci

    def test_script_suelto_corre_solo_sus_tests(self):
        refs = {'rebase-regenerando': {'scripts/rebase-regenerando.py', 'tests/test_rebase_regenerando.py'}}
        items = self.ci.scoped({'scripts/rebase-regenerando.py'}, refs=lambda s: refs[s])
        self.assertEqual([c for c, *_ in items], [
            'python -m py_compile scripts/rebase-regenerando.py',
            'python -m unittest discover -s tests -p test_rebase_regenerando.py'])

    def test_script_usado_por_un_workflow_va_por_la_via_completa(self):
        refs = {'build-sitemap': {'.github/workflows/content-index-check.yml', 'tests/test_sitemap.py'}}
        self.assertIsNone(self.ci.scoped({'scripts/build-sitemap.py'}, refs=lambda s: refs[s]))

    def test_otro_fichero_va_por_la_via_completa(self):
        self.assertIsNone(self.ci.scoped({'scripts/x.py', 'data/reading-books.json'}, refs=lambda s: set()))


class ServidoresVigilados(unittest.TestCase):
    def test_un_servidor_caido_se_relanza(self):
        import socket
        import tempfile
        with socket.socket() as s:
            s.bind(('127.0.0.1', 0))
            port = s.getsockname()[1]
        old = local_ci.PORTS
        local_ci.PORTS = (port,)
        try:
            with tempfile.TemporaryDirectory() as root, \
                    local_ci.Servers(root, lock_path=Path(root) / 'ports.lock') as servers:
                self.assertTrue(servers.alive(port))
                servers.procs[port].kill()
                servers.procs[port].wait()
                servers.ensure()
                self.assertEqual(servers.restarts, 1)
                self.assertTrue(servers.alive(port))
        finally:
            local_ci.PORTS = old


class EntornoDelCI(unittest.TestCase):
    def test_un_entorno_a_medias_se_rehace(self):
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'scripts').mkdir()
            (root / 'scripts/requirements.txt').write_text('Pillow==12.3.0\n', encoding='utf-8')
            pips = []

            def run(cmd, **_):
                if 'venv' in cmd:
                    exe = Path(cmd[-1]) / ('Scripts/python.exe' if local_ci.os.name == 'nt' else 'bin/python')
                    exe.parent.mkdir(parents=True)
                    exe.write_text('')
                elif 'pip' in cmd:
                    pips.append(cmd)
                    if len(pips) == 1:
                        raise KeyboardInterrupt  # puerta cortada a mitad del pip install

            with mock.patch.object(local_ci, 'ROOT', root), mock.patch.object(local_ci.subprocess, 'run', run):
                with self.assertRaises(KeyboardInterrupt):
                    local_ci.ci_python()
                local_ci.ci_python()                    # python.exe existe pero sin marca: se rehace
                self.assertEqual(len(pips), 2)
                local_ci.ci_python()                    # con la marca no se reinstala
                self.assertEqual(len(pips), 2)


class NodeModulesDelWorktree(unittest.TestCase):
    def test_un_worktree_nuevo_enlaza_los_del_checkout_principal(self):
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            principal, wt = Path(d) / 'principal', Path(d) / 'wt'
            principal.mkdir()
            git = lambda *a, cwd=principal: subprocess.run(['git', *a], cwd=cwd, check=True, capture_output=True)
            git('init', '-q')
            (principal / 'package-lock.json').write_text('{}', encoding='utf-8')
            git('add', '.')
            git('-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '-m', 'x')
            (principal / 'node_modules/playwright').mkdir(parents=True)
            git('worktree', 'add', '-q', '--detach', str(wt))
            local_ci.node_modules_listos(wt)
            self.assertTrue((wt / 'node_modules/playwright').exists())
            local_ci.node_modules_listos(wt)            # ya están: no hace nada
            if local_ci.os.name == 'nt':                # quitar la unión sin borrar el destino
                subprocess.run(['cmd', '/c', 'rmdir', str(wt / 'node_modules')], check=True)
            else:
                (wt / 'node_modules').unlink()


class CerrojoDePuertos(unittest.TestCase):
    def test_una_segunda_puerta_espera(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'ports.lock'
            first = local_ci.ports_lock(path)
            with self.assertRaises(SystemExit):
                local_ci.ports_lock(path, wait=0)
            local_ci.release(first)
            local_ci.release(local_ci.ports_lock(path, wait=0))


if __name__ == '__main__':
    unittest.main()
