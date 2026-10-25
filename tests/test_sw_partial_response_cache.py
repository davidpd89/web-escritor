import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
JS = r'''
const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
const handlers = {};
let writes = 0;
const ctx = {
  URL, Request, Response, Set, console,
  caches: {open: async () => ({
    put: async () => {writes++},
    match: async () => undefined
  })},
  fetch: async () => new Response('partial', {
    status: 206,
    headers: {'Content-Range': 'bytes 0-6/100'}
  }),
  self: {
    location: {origin: 'https://example.test'},
    addEventListener: (name, fn) => handlers[name] = fn
  }
};
vm.runInNewContext(fs.readFileSync('service-worker.js', 'utf8'), ctx);
(async () => {
  const request = new Request('https://example.test/assets/app.js');
  let pending;
  handlers.fetch({request, respondWith: p => pending = p});
  assert(pending);
  const response = await pending;
  assert.strictEqual(response.status, 206);
  assert.strictEqual(writes, 0, 'HTTP 206 response was cached');
})().catch(e => {console.error(e); process.exitCode = 1});
'''

class TestPartialResponse(unittest.TestCase):
    def test_partial_response_not_cached(self):
        p = subprocess.run(['node', '-e', JS], cwd=ROOT, capture_output=True, text=True, timeout=20)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

if __name__ == '__main__':
    unittest.main()
