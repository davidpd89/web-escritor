import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
JS = r'''
const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
const handlers = {};
const keys = new Set([
  'david-porto-pwa-v1-static',
  'david-porto-pwa-v15-pages',
  'david-porto-pwa-v16-static',
  'david-porto-pwa-v16-pages',
  'other-app-v1',
  'david-porto-pwa-backup'
]);
const deleted = [];
const ctx = {
  URL, Request, Response, Set, console,
  caches: {
    keys: async () => [...keys],
    delete: async key => {deleted.push(key); return keys.delete(key)}
  },
  self: {
    location: {origin: 'https://example.test'},
    addEventListener: (name, fn) => handlers[name] = fn,
    clients: {claim: async () => {}}
  }
};
vm.runInNewContext(fs.readFileSync('service-worker.js', 'utf8'), ctx);
(async () => {
  let pending;
  handlers.activate({waitUntil: p => pending = p});
  await pending;
  assert(!keys.has('david-porto-pwa-v1-static'));
  assert(!keys.has('david-porto-pwa-v15-pages'));
  assert(keys.has('david-porto-pwa-v16-static'));
  assert(keys.has('david-porto-pwa-v16-pages'));
  assert(keys.has('other-app-v1'));
  assert(!deleted.includes('other-app-v1'));
})().catch(e => {console.error(e); process.exitCode = 1});
'''

class TestCacheActivation(unittest.TestCase):
    def test_namespace_isolation(self):
        p = subprocess.run(['node', '-e', JS], cwd=ROOT, capture_output=True, text=True, timeout=20)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

if __name__ == '__main__':
    unittest.main()
