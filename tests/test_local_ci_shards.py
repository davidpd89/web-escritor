import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('local_ci', ROOT / 'scripts' / 'local-ci.py')
local_ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(local_ci)


class Lotes(unittest.TestCase):
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
