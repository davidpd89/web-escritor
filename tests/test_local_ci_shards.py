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


if __name__ == '__main__':
    unittest.main()


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
            with tempfile.TemporaryDirectory() as root, local_ci.Servers(root) as servers:
                self.assertTrue(servers.alive(port))
                servers.procs[port].kill()
                servers.procs[port].wait()
                servers.ensure()
                self.assertEqual(servers.restarts, 1)
                self.assertTrue(servers.alive(port))
        finally:
            local_ci.PORTS = old
