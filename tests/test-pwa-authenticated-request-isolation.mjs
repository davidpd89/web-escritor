import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const listeners = new Map();
const entries = new Map();
let networkCalls = 0;
const cache = {
  match: async request => entries.get(request.url)?.clone() || null,
  put: async (request, response) => entries.set(request.url, response.clone())
};
const sandbox = {
  URL, Request, Response, Headers, console,
  caches: { open: async () => cache },
  fetch: async request => {
    networkCalls++;
    return new Response(`network-${networkCalls}`, { status: 200 });
  },
  self: {
    location: { origin: 'https://davidportodiaz.com' },
    addEventListener: (type, callback) => listeners.set(type, callback)
  }
};
vm.runInNewContext(fs.readFileSync('service-worker.js', 'utf8'), sandbox);
const handler = listeners.get('fetch');

async function requestFor(token) {
  let promise;
  const waits = [];
  handler({
    request: {
      method: 'GET',
      url: 'https://davidportodiaz.com/__qa_account/',
      mode: 'navigate',
      destination: 'document',
      headers: new Headers({ Authorization: `Bearer ${token}` })
    },
    respondWith: value => { promise = Promise.resolve(value); },
    waitUntil: value => waits.push(Promise.resolve(value))
  });
  if (!promise) return { intercepted: false };
  const response = await promise;
  await Promise.all(waits);
  return { intercepted: true, body: await response.text() };
}

const first = await requestFor('USER_A');
const second = await requestFor('USER_B');
assert.equal(entries.size, 0, 'Authenticated pages persisted in shared CacheStorage');
assert.ok(!first.intercepted || first.body !== second.body, 'Cross-user cached response reused');
console.log('PASS: authenticated requests isolated');