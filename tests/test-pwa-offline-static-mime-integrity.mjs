import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const listeners = new Map();
const entries = new Map();
let online = true;
const sandbox = {
  URL, Request, Response, Headers, console,
  caches: {
    open: async () => ({
      match: async req => entries.get(req.url || req)?.clone() || null,
      put: async (req, response) => entries.set(req.url || req, response.clone()),
      addAll: async () => {}
    }),
    keys: async () => [], delete: async () => true
  },
  fetch: async req => {
    if (!online) throw new TypeError('Offline');
    const extension = new URL(req.url).pathname.split('.').pop();
    const type = extension === 'css' ? 'text/css' : 'text/javascript';
    return new Response('VALID-' + extension, { status: 200, headers: { 'Content-Type': type } });
  },
  self: {
    location: { origin: 'https://davidportodiaz.com' },
    addEventListener: (type, fn) => listeners.set(type, fn),
    skipWaiting: async () => {}, clients: { claim: async () => {} }
  }
};
vm.runInNewContext(fs.readFileSync('service-worker.js', 'utf8'), sandbox);
async function request(path) {
  let promise;
  listeners.get('fetch')({
    request: { method: 'GET', url: 'https://davidportodiaz.com' + path, mode: 'cors', destination: 'script', headers: new Headers() },
    respondWith: p => { promise = p; }, waitUntil: () => {}
  });
  assert.ok(promise);
  return promise;
}
for (const extension of ['css', 'js', 'mjs']) {
  const path = '/assets/offline-test.' + extension;
  const live = await request(path);
  assert.equal(live.status, 200);
  online = false;
  const cached = await request(path);
  assert.equal(cached.status, 200);
  assert.equal(await cached.text(), 'VALID-' + extension);
  assert.match(cached.headers.get('content-type'), extension === 'css' ? /text\/css/ : /javascript/);
  const missing = await request('/assets/not-cached-' + extension + '.' + extension);
  assert.equal(missing.status, 504);
  assert.equal(await missing.text(), 'Offline');
  assert.doesNotMatch(missing.headers.get('content-type') || '', /text\/html/);
  online = true;
}
console.log('PASS: CSS, JS y MJS mantienen bytes y MIME al quedar sin red');