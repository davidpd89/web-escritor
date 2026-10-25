import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const listeners = new Map();
let writes = 0;
let matches = 0;
const cache = {
  match: async () => { matches++; return new Response('STALE'); },
  put: async () => { writes++; },
  addAll: async () => {}
};
const sandbox = {
  URL, Request, Response, Headers, console,
  caches: { open: async () => cache, keys: async () => [], delete: async () => true },
  fetch: async () => new Response('SERVER_ERROR', {
    status: 500,
    headers: { 'X-Error-Id': 'test-500' }
  }),
  self: {
    location: { origin: 'https://davidportodiaz.com' },
    addEventListener: (type, handler) => listeners.set(type, handler),
    skipWaiting: async () => {},
    clients: { claim: async () => {} }
  }
};
vm.runInNewContext(fs.readFileSync('service-worker.js', 'utf8'), sandbox);
for (const [path, mode] of [['/autor.html', 'navigate'], ['/assets/app.js', 'cors']]) {
  let responsePromise;
  listeners.get('fetch')({
    request: { method: 'GET', url: `https://davidportodiaz.com${path}`, mode, destination: '', headers: new Headers() },
    respondWith: promise => { responsePromise = promise; },
    waitUntil: () => {}
  });
  assert.ok(responsePromise);
  const response = await responsePromise;
  assert.equal(response.status, 500);
  assert.equal(response.headers.get('X-Error-Id'), 'test-500');
  assert.equal(await response.text(), 'SERVER_ERROR');
}
assert.equal(writes, 0);
assert.equal(matches, 0);
console.log('PASS: HTTP 500 preserved without stale fallback');