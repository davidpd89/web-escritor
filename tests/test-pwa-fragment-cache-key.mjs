import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const listeners = new Map();
const stored = new Map();
const keyOf = request => {
  const url = new URL(request.url);
  url.hash = '';
  return url.href;
};
const cache = {
  match: async request => stored.get(keyOf(request))?.clone() || null,
  put: async (request, response) => stored.set(keyOf(request), response.clone())
};
const sandbox = {
  URL, Request, Response, Headers, console,
  caches: { open: async () => cache },
  fetch: async () => new Response('PAGE_CONTENT', { status: 200 }),
  self: {
    location: { origin: 'https://davidportodiaz.com' },
    addEventListener: (name, handler) => listeners.set(name, handler)
  }
};
vm.runInNewContext(fs.readFileSync('service-worker.js', 'utf8'), sandbox);
const handler = listeners.get('fetch');
for (const fragment of ['chapter-one', 'chapter-two', '']) {
  let promise;
  const waits = [];
  handler({
    request: {
      method: 'GET',
      url: `https://davidportodiaz.com/libros/#${fragment}`,
      mode: 'navigate',
      destination: 'document',
      headers: new Headers()
    },
    respondWith: value => { promise = Promise.resolve(value); },
    waitUntil: value => waits.push(Promise.resolve(value))
  });
  assert.ok(promise);
  assert.equal((await promise).status, 200);
  await Promise.all(waits);
}
assert.equal(stored.size, 1, 'URL fragments generated duplicate cache keys');
console.log('PASS: fragments do not multiply cache entries');