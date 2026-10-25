import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const listeners = new Map();
let networkCalls = 0;
const sandbox = {
  URL, Request, Response, Headers, console,
  caches: {
    open: async () => {throw new Error('CacheStorage unavailable');},
    keys: async () => [],
    delete: async () => true
  },
  fetch: async () => {networkCalls++; return new Response('<h1>Contenido disponible</h1>', {status: 200});},
  self: {location: {origin: 'https://davidportodiaz.com'}, addEventListener: (type, fn) => listeners.set(type, fn), skipWaiting: async () => {}, clients: {claim: async () => {}}}
};
vm.runInNewContext(fs.readFileSync('service-worker.js', 'utf8'), sandbox);
for (const [path, mode] of [['/libros/', 'navigate'], ['/assets/main.js', 'cors']]) {
  let result;
  listeners.get('fetch')({
    request: {method: 'GET', url: `https://davidportodiaz.com${path}`, mode, destination: mode === 'navigate' ? 'document' : 'script', headers: new Headers()},
    respondWith: promise => {result = promise;},
    waitUntil: () => {}
  });
  assert.ok(result, `Sin respuesta para ${path}`);
  const response = await result;
  assert.equal(response.status, 200, `La red debe seguir disponible para ${path}`);
  assert.match(await response.text(), /Contenido disponible/);
}
assert.equal(networkCalls, 2);
console.log('PASS: recuperación sin CacheStorage');