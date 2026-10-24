import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const listeners = new Map();
let writes = 0;
const cache = {
  match: async () => null,
  put: async (_request, response) => {
    writes++;
    if (response.status === 206) throw new TypeError('Cache.put rejects partial responses');
  },
  addAll: async () => {}
};
const sandbox = {
  URL, Request, Response, Headers, console,
  caches: { open: async () => cache, keys: async () => [], delete: async () => true },
  fetch: async () => new Response('PARTIAL-BYTES', {
    status: 206,
    headers: { 'Content-Range': 'bytes 0-12/100', 'Content-Type': 'text/javascript' }
  }),
  self: {
    location: { origin: 'https://davidportodiaz.com' },
    addEventListener: (type, callback) => listeners.set(type, callback),
    skipWaiting: async () => {},
    clients: { claim: async () => {} }
  }
};
vm.runInNewContext(readFileSync('service-worker.js', 'utf8'), sandbox);
let responsePromise;
listeners.get('fetch')({
  request: {
    method: 'GET',
    url: 'https://davidportodiaz.com/assets/partial.js',
    mode: 'cors',
    destination: 'script',
    headers: new Headers()
  },
  respondWith: promise => { responsePromise = promise; },
  waitUntil: () => {}
});
assert.ok(responsePromise, 'El worker no respondió a la petición');
const result = await responsePromise;
assert.equal(result.status, 206, 'El fallo de almacenamiento no debe ocultar la respuesta original');
assert.equal(await result.text(), 'PARTIAL-BYTES');
assert.ok(writes <= 1);
console.log('PASS: HTTP 206 conservado aunque CacheStorage rechace el almacenamiento');