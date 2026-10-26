import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const origin = 'https://davidportodiaz.com';
const listeners = new Map();
let cacheAccesses = 0;
let networkCalls = 0;
const sandbox = {
  URL, Request, Response, Headers, Promise, Set, console,
  caches: {
    open: async () => {
      cacheAccesses++;
      throw new Error('API no debe acceder a CacheStorage');
    }
  },
  fetch: async () => {
    networkCalls++;
    return new Response('{}');
  },
  self: {
    location: {origin},
    addEventListener: (type, callback) => listeners.set(type, callback)
  }
};
vm.runInNewContext(readFileSync('service-worker.js', 'utf8'), sandbox);
const handler = listeners.get('fetch');
assert.equal(typeof handler, 'function', 'service-worker.js: falta el manejador fetch');
for (const path of ['/api', '/api/']) {
  let intercepted = false;
  handler({
    request: new Request(origin + path),
    respondWith() {intercepted = true;},
    waitUntil() {intercepted = true;}
  });
  assert.equal(intercepted, false, path + ': el SW interceptó un endpoint API');
}
assert.equal(cacheAccesses, 0, '/api: se abrió CacheStorage');
assert.equal(networkCalls, 0, '/api: el SW gestionó directamente la red en lugar de dejarla al navegador');
console.log('PASS: SW API cache isolation');