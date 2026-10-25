import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const listeners = new Map();
let writes = 0;
const original = new Response('CSS ORIGINAL', {status: 200});
const cache = {
  match: async () => original.clone(),
  put: async () => {writes++;},
  addAll: async () => {}
};
const sandbox = {
  URL, Request, Response, Headers, console,
  caches: {open: async () => cache, keys: async () => [], delete: async () => true},
  fetch: async () => new Response(null, {status: 304}),
  self: {location: {origin: 'https://davidportodiaz.com'}, addEventListener: (type, fn) => listeners.set(type, fn), skipWaiting: async () => {}, clients: {claim: async () => {}}}
};
vm.runInNewContext(fs.readFileSync('service-worker.js', 'utf8'), sandbox);
let responsePromise;
listeners.get('fetch')({
  request: {method: 'GET', url: 'https://davidportodiaz.com/assets/estilos.css', mode: 'cors', destination: 'style', headers: new Headers({'If-None-Match': '"old"'})},
  respondWith: promise => {responsePromise = promise;},
  waitUntil: () => {}
});
assert.ok(responsePromise);
const response = await responsePromise;
assert.equal(response.status, 200, 'Debe entregarse la representación completa almacenada');
assert.equal(await response.text(), 'CSS ORIGINAL');
assert.equal(writes, 0, 'HTTP 304 no debe sustituir el recurso');
console.log('PASS: HTTP 304 conserva la representación completa');