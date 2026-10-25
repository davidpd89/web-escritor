import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const listeners = new Map();
const sandbox = {
  URL, Request, Response, Headers, console,
  caches: { open: async () => ({ match: async () => null, put: async () => {} }) },
  fetch: async () => new Response('ok'),
  self: {
    location: { origin: 'https://davidportodiaz.com' },
    addEventListener: (type, callback) => listeners.set(type, callback),
    clients: { claim: async () => {} },
    skipWaiting: async () => {}
  }
};
vm.runInNewContext(fs.readFileSync('service-worker.js', 'utf8'), sandbox);
function intercepted(path) {
  let called = false;
  listeners.get('fetch')({
    request: { method: 'GET', url: `https://davidportodiaz.com${path}`, mode: 'cors', destination: '', headers: new Headers() },
    respondWith: () => { called = true; },
    waitUntil: () => {}
  });
  return called;
}
for (const path of ['/api?token=secret', '/api/?page=2', '/api/assistant?x=1', '/api/%61ssistant', '/api/assistant/config#test']) {
  assert.equal(intercepted(path), false, `${path} must bypass`);
}
for (const path of ['/apiary', '/api-v2', '/assets/api-client.js', '/api.html']) {
  assert.equal(intercepted(path), true, `${path} must remain intercepted`);
}
console.log('PASS: API boundaries');