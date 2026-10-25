import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const listeners = new Map();
const stored = new Map();
const cache = {
  match: async request => stored.get(request.url)?.clone() || null,
  put: async (request, response) => stored.set(request.url, response.clone())
};
const sandbox = {
  URL, Request, Response, Headers, console,
  caches: { open: async () => cache },
  fetch: async () => new Response('IDENTICAL_PAGE', { status: 200 }),
  self: {
    location: { origin: 'https://davidportodiaz.com' },
    addEventListener: (name, callback) => listeners.set(name, callback)
  }
};
vm.runInNewContext(fs.readFileSync('service-worker.js', 'utf8'), sandbox);
const handler = listeners.get('fetch');
const variants = [
  '/libros/',
  '/libros/?utm_source=threads',
  '/libros/?utm_source=pinterest',
  '/libros/?utm_campaign=autumn',
  '/libros/?fbclid=example',
  '/libros/?gclid=example'
];
for (const path of variants) {
  let promise;
  handler({
    request: {
      method: 'GET',
      url: `https://davidportodiaz.com${path}`,
      mode: 'navigate',
      destination: 'document',
      headers: new Headers()
    },
    respondWith: value => { promise = Promise.resolve(value); },
    waitUntil: () => {}
  });
  assert.ok(promise);
  assert.equal((await promise).status, 200);
}
assert.equal(stored.size, 1, `Tracking parameters created ${stored.size} cached page variants`);
console.log('PASS: tracking parameters do not multiply page cache entries');