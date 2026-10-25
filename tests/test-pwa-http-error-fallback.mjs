import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const listeners = new Map();
let writes = 0;
const cache = {
  match: async () => new Response('<h1>Versión disponible</h1>', {status: 200}),
  put: async () => { writes++; },
  addAll: async () => {}
};
const sandbox = {
  URL, Request, Response, Headers, console,
  caches: {open: async () => cache, keys: async () => [], delete: async () => true},
  fetch: async () => new Response('Servicio no disponible', {status: 503}),
  self: {
    location: {origin: 'https://davidportodiaz.com'},
    addEventListener: (type, fn) => listeners.set(type, fn),
    skipWaiting: async () => {},
    clients: {claim: async () => {}}
  }
};
vm.runInNewContext(fs.readFileSync('service-worker.js', 'utf8'), sandbox);
let result;
listeners.get('fetch')({
  request: {method: 'GET', url: 'https://davidportodiaz.com/libros/', mode: 'navigate', destination: 'document', headers: new Headers()},
  respondWith: promise => {result = promise;},
  waitUntil: () => {}
});
assert.ok(result, 'La navegación debe estar interceptada');
const response = await result;
assert.equal(response.status, 200, 'Debe recuperarse la copia válida ante HTTP 503');
assert.match(await response.text(), /Versión disponible/);
assert.equal(writes, 0, 'No debe almacenarse HTTP 503');
console.log('PASS: recuperación ante HTTP 503');