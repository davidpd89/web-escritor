import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

JS = r'''
const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
const source = fs.readFileSync('service-worker.js', 'utf8');
const writes = [];
const cache = {
  put: async (req, res) => writes.push(req.url),
  match: async () => undefined
};
const handlers = {};
const context = {
  URL, Request, Response, Set,
  console,
  caches: {open: async () => cache},
  fetch: async () => new Response('private content', {
    status: 200,
    headers: {
      'Cache-Control': 'private, max-age=600',
      'Set-Cookie': 'session=secret; HttpOnly'
    }
  }),
  self: {
    location: {origin: 'https://example.test'},
    addEventListener: (name, fn) => handlers[name] = fn
  }
};
vm.runInNewContext(source, context);
(async () => {
  const req = new Request('https://example.test/private.html');
  Object.defineProperty(req, 'mode', {value: 'navigate'});
  let result;
  handlers.fetch({request: req, respondWith: p => result = p});
  assert(result, 'navigation was not intercepted');
  await result;
  assert.deepStrictEqual(writes, [], 'private response was cached');
})().catch(e => {console.error(e); process.exitCode = 1});
'''

class TestPrivateCache(unittest.TestCase):
    def test_private_responses_never_cached(self):
        result = subprocess.run(['node', '-e', JS], cwd=ROOT, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

if __name__ == '__main__':
    unittest.main()
