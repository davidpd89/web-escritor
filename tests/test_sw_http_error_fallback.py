import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
JS = r'''
const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
const handlers = {};
const entries = new Map();
let status = 200;
let disconnected = false;
const cache = {
  put: async (req, response) => entries.set(req.url, response.clone()),
  match: async req => entries.get(typeof req === 'string' ? req : req.url)?.clone()
};
const ctx = {
  URL, Request, Response, Set, console,
  caches: {open: async () => cache},
  fetch: async () => {
    if (disconnected) throw Error('offline');
    return new Response(status === 200 ? 'valid page' : 'server error', {status});
  },
  self: {
    location: {origin: 'https://example.test'},
    addEventListener: (name, fn) => handlers[name] = fn
  }
};
vm.runInNewContext(fs.readFileSync('service-worker.js', 'utf8'), ctx);
const request = new Request('https://example.test/article/');
Object.defineProperty(request, 'mode', {value: 'navigate'});
async function navigate() {
  let response;
  handlers.fetch({request, respondWith: p => response = p});
  assert(response);
  return await response;
}
(async () => {
  assert.strictEqual(await (await navigate()).text(), 'valid page');
  for (const errorStatus of [404, 500]) {
    status = errorStatus;
    assert.strictEqual((await navigate()).status, errorStatus);
    disconnected = true;
    const fallback = await navigate();
    assert.strictEqual(fallback.status, 200);
    assert.strictEqual(await fallback.text(), 'valid page');
    disconnected = false;
  }
})().catch(e => {console.error(e); process.exitCode = 1});
'''

class TestHttpErrorFallback(unittest.TestCase):
    def test_http_errors_do_not_poison_cache(self):
        p = subprocess.run(['node', '-e', JS], cwd=ROOT, capture_output=True, text=True, timeout=20)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

if __name__ == '__main__':
    unittest.main()
