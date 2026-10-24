import hashlib
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = '''import importlib.util,hashlib,json,pathlib
root=pathlib.Path.cwd()
def load(name,file):
 s=importlib.util.spec_from_file_location(name,root/'scripts'/file)
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
sm=load('sitemap_probe','build-sitemap.py')
fd=load('feed_probe','build-feed.py')
urls=sm.render_xml(sm.collect_urls(root)).encode('utf-8')
items,_=fd.collect_items()
feed=fd.build_feed_bytes(items)
print(json.dumps({'sitemap':hashlib.sha256(urls).hexdigest(),'feed':hashlib.sha256(feed).hexdigest(),'count':len(items)},sort_keys=True))
'''

class ReproducibilityTests(unittest.TestCase):
    def test_environment_independent_generation(self):
        results = []
        for zone, seed in [('UTC','0'), ('Europe/Madrid','1'),
                           ('Asia/Tokyo','123'), ('America/Los_Angeles','999')]:
            with self.subTest(zone=zone, seed=seed):
                env = dict(os.environ, TZ=zone, PYTHONHASHSEED=seed)
                run = subprocess.run([sys.executable, '-c', PROBE], cwd=ROOT,
                    env=env, text=True, capture_output=True, timeout=90)
                self.assertEqual(run.returncode, 0, run.stderr)
                results.append(run.stdout.strip())
        self.assertTrue(results)
        self.assertTrue(all(result == results[0] for result in results), results)

if __name__ == '__main__':
    unittest.main()
