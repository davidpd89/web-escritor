import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const listeners = new Map();
let attempts = 0;
const cache = {
  match: async () => null,
  put: async () => { attempts++; throw new Error('QuotaExceededError'); },
  addAll: async () => {}
};
const sandbox = {
  URL, Request, Response, Headers,
  console: { ...console, warn: () => {} },
  caches: { open: async () => cache },
  fetch: async () => new Response('FRESH', { status: 200, headers: { 'Content-Type': 'text/javascript' } }),
  self: {
    location: { origin: 'https://davidportodiaz.com' },
    addEventListener: (type, callback) => listeners.set(type, callback),
    skipWaiting: async () => {},
    clients: { claim: async () => {} }
  }
};
vm.runInNewContext(fs.readFileSync('service-worker.js', 'utf8'), sandbox);
for (const [path, mode] of [['/assets/main.js', 'cors'], ['/autor.html', 'navigate']]) {
  let promise;
  listeners.get('fetch')({
    request: { method: 'GET', url: `https://davidportodiaz.com${path}`, mode, destination: '', headers: new Headers() },
    respondWith: p => { promise = p; },
    waitUntil: () => {}
  });
  const response = await promise;
  assert.equal(response.status, 200);
  assert.equal(await response.text(), 'FRESH');
}
assert.equal(attempts, 2);
console.log('PASS: failed cache writes preserve network responses');