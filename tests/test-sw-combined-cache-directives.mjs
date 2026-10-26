import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const origin = 'https://davidportodiaz.com';
const cases = [
  'public, max-age=3600, no-store',
  'max-age=60, private',
  'private, must-revalidate',
  'no-store, max-age=0'
];

for (const policy of cases) {
  const listeners = new Map();
  const writes = [];
  let networkCalls = 0;
  const cache = {
    match: async () => null,
    put: async request => {writes.push(request.url);},
    addAll: async () => {}
  };
  const sandbox = {
    URL, Request, Response, Headers, console,
    caches: {
      open: async () => cache,
      keys: async () => [],
      delete: async () => true
    },
    fetch: async () => {
      networkCalls++;
      return new Response('<main>Contenido público</main>', {
        status: 200,
        headers: {'Cache-Control': policy, 'Content-Type': 'text/html'}
      });
    },
    self: {
      location: {origin},
      addEventListener: (type, callback) => listeners.set(type, callback),
      skipWaiting: async () => {},
      clients: {claim: async () => {}}
    }
  };
  vm.runInNewContext(readFileSync('service-worker.js', 'utf8'), sandbox);
  let pending;
  const pathname = '/cuaderno/';
  listeners.get('fetch')({
    request: {method: 'GET', url: origin + pathname, mode: 'navigate', destination: 'document', headers: new Headers()},
    respondWith(promise) {pending = promise;},
    waitUntil() {}
  });
  assert.ok(pending, `${pathname}: falta respuesta para ${policy}`);
  const response = await pending;
  assert.equal(response.status, 200, `${pathname}: HTTP incorrecto para ${policy}`);
  assert.equal(networkCalls, 1, `${pathname}: peticiones inesperadas para ${policy}`);
  assert.equal(writes.length, 0, `${pathname}: Cache-Control ${policy} permitió almacenar ${JSON.stringify(writes)}`);
}
console.log('PASS combined restrictive Cache-Control policies');