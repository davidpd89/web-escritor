import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const listeners = new Map();
let writes = 0;
let directive = 'no-store';
const cache = {
  match: async () => null,
  put: async () => { writes++; },
  addAll: async () => {}
};
const sandbox = {
  URL, Request, Response, Headers, console,
  caches: { open: async () => cache },
  fetch: async () => new Response('PRIVATE_DATA', {
    status: 200,
    headers: { 'Cache-Control': directive }
  }),
  self: {
    location: { origin: 'https://davidportodiaz.com' },
    addEventListener: (type, callback) => listeners.set(type, callback),
    skipWaiting: async () => {},
    clients: { claim: async () => {} }
  }
};
vm.runInNewContext(fs.readFileSync('service-worker.js', 'utf8'), sandbox);
for (directive of ['no-store', 'private, max-age=0', 'no-cache, no-store']) {
  const before = writes;
  let promise;
  listeners.get('fetch')({
    request: { method: 'GET', url: 'https://davidportodiaz.com/private.json', mode: 'cors', destination: '', headers: new Headers() },
    respondWith: p => { promise = p; },
    waitUntil: () => {}
  });
  const response = await promise;
  assert.equal(response.status, 200);
  assert.equal(await response.text(), 'PRIVATE_DATA');
  assert.equal(writes, before, `Response with ${directive} must not be cached`);
}
console.log('PASS: private responses are not cached');