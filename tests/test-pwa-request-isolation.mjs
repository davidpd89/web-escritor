import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const listeners = new Map();
let opens = 0;
const sandbox = {
  URL, Request, Response, Headers, console,
  caches: { open: async () => { opens++; return { match: async () => null, put: async () => {} }; } },
  fetch: async () => new Response('ok'),
  self: {
    location: { origin: 'https://davidportodiaz.com' },
    addEventListener: (type, callback) => listeners.set(type, callback),
    skipWaiting: async () => {},
    clients: { claim: async () => {} }
  }
};
vm.runInNewContext(fs.readFileSync('service-worker.js', 'utf8'), sandbox);
function intercepted(method, url) {
  let called = false;
  listeners.get('fetch')({
    request: { method, url, mode: 'cors', destination: '', headers: new Headers() },
    respondWith: () => { called = true; },
    waitUntil: () => {}
  });
  return called;
}
const own = 'https://davidportodiaz.com/assets/data.json';
for (const method of ['POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']) {
  assert.equal(intercepted(method, own), false, method);
}
for (const url of ['https://example.org/assets/app.js', 'https://davidportodiaz.com.evil.example/assets/app.js', 'http://davidportodiaz.com/assets/app.js', 'https://sub.davidportodiaz.com/assets/app.js']) {
  assert.equal(intercepted('GET', url), false, url);
}
assert.equal(opens, 0);
assert.equal(intercepted('GET', own), true);
console.log('PASS: request isolation');