import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const listeners = new Map();
const writes = [];
let networkResponse;
const cache = {
  match: async () => null,
  put: async (request, response) => {
    writes.push({ url: request.url, response });
  }
};
const sandbox = {
  URL, Request, Response, Headers, console,
  caches: { open: async () => cache },
  fetch: async () => networkResponse,
  self: {
    location: { origin: 'https://davidportodiaz.com' },
    addEventListener: (name, callback) => listeners.set(name, callback)
  }
};
vm.runInNewContext(fs.readFileSync('service-worker.js', 'utf8'), sandbox);
const fetchHandler = listeners.get('fetch');
assert.equal(typeof fetchHandler, 'function');

async function dispatch(path, headers) {
  networkResponse = new Response('PRIVATE_CONTENT', { status: 200, headers });
  let responsePromise;
  const waits = [];
  fetchHandler({
    request: {
      method: 'GET',
      url: `https://davidportodiaz.com${path}`,
      mode: 'navigate',
      destination: 'document',
      headers: new Headers()
    },
    respondWith: promise => { responsePromise = Promise.resolve(promise); },
    waitUntil: promise => waits.push(Promise.resolve(promise))
  });
  assert.ok(responsePromise);
  const response = await responsePromise;
  await Promise.all(waits);
  assert.equal(response.status, 200);
}

const cases = [
  { 'Cache-Control': 'private, max-age=0' },
  { 'Cache-Control': 'no-store' },
  { 'Cache-Control': 'public, no-cache, no-store' },
  { 'Set-Cookie': 'session=private; HttpOnly; Secure' }
];
for (const [index, headers] of cases.entries()) {
  writes.length = 0;
  await dispatch(`/__qa_private_${index}/`, headers);
  assert.equal(writes.length, 0, `Private response cached for case ${index}`);
}
console.log('PASS: private responses never persisted');