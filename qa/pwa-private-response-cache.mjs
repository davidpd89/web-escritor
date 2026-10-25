import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const handlers = {};
const writes = [];
const cache = {
  put: async (request, response) => writes.push({ url: request.url, response }),
  match: async () => undefined
};
const caches = { open: async () => cache };
let responseHeaders = { 'Cache-Control': 'no-store' };
const self = {
  location: { origin: 'https://local.test' },
  addEventListener: (type, handler) => { handlers[type] = handler; }
};
vm.runInNewContext(readFileSync('service-worker.js', 'utf8'), {
  self, caches, URL, Headers, Request, Response,
  fetch: async () => new Response('PRIVATE DATA', {
    status: 200,
    headers: responseHeaders
  })
});

async function navigate(path) {
  let result;
  const request = {
    url: `https://local.test${path}`,
    method: 'GET', mode: 'navigate', destination: 'document', headers: new Headers()
  };
  handlers.fetch({
    request,
    respondWith: promise => { result = promise; },
    waitUntil: () => {}
  });
  const response = await result;
  assert.equal(response.status, 200);
  assert.equal(await response.text(), 'PRIVATE DATA');
}

await navigate('/lectores-beta/?session=abc');
assert.equal(writes.length, 0, 'no-store response persisted in CacheStorage');
responseHeaders = { 'Cache-Control': 'private, no-store' };
await navigate('/herramientas/?session=xyz');
assert.equal(writes.length, 0, 'private no-store response persisted in CacheStorage');
console.log('PASS: private and no-store responses never persisted');
