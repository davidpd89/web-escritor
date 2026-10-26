import assert from 'node:assert/strict';
import vm from 'node:vm';
import { readFileSync } from 'node:fs';

const handlers = {};
let cacheCalls = 0;
let networkCalls = 0;
const origin = 'https://local.test';
const self = {
  location: { origin },
  addEventListener: (name, handler) => { handlers[name] = handler; }
};
vm.runInNewContext(readFileSync('service-worker.js', 'utf8'), {
  self, URL, Request, Response, Headers, console,
  caches: {
    open: async () => { cacheCalls++; throw new Error('CacheStorage no debe utilizarse'); }
  },
  fetch: async request => {
    networkCalls++;
    return new Response('RED ACTUAL', { status: 200 });
  }
});

for (const path of ['/sitemap.xml', '/editoriales/', '/assets/v1-base.css']) {
  const request = new Request(origin + path, { cache: 'no-store' });
  let pending;
  handlers.fetch({
    request,
    respondWith: response => { pending = response; },
    waitUntil: () => {}
  });
  assert.ok(pending, `${path}: no se interceptó la petición no-store`);
  const response = await pending;
  assert.equal(response.status, 200, `${path}: HTTP incorrecto`);
  assert.equal(await response.text(), 'RED ACTUAL', `${path}: respuesta no procedente de la red`);
}
assert.equal(cacheCalls, 0, 'CacheStorage: se consultó durante una petición no-store');
assert.equal(networkCalls, 3, 'service-worker.js: número incorrecto de peticiones de red');
console.log('PASS no-store cache bypass');