import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const origin = 'https://davidportodiaz.com';
const assets = [
  ['/assets/david-porto-favicon.png', 'image', 'image/png'],
  ['/assets/fonts/is-normal-400-latin.woff2', 'font', 'font/woff2']
];

for (const [pathname, destination, mime] of assets) {
  const listeners = new Map();
  let calls = 0;
  const payload = new Uint8Array([12, 34, 56, 78]);
  const sandbox = {
    URL, Request, Response, Headers, console,
    caches: {
      open: async () => { throw new Error('Storage unavailable'); },
      keys: async () => [],
      delete: async () => true
    },
    fetch: async () => {
      calls++;
      return new Response(payload, {status: 200, headers: {'Content-Type': mime}});
    },
    self: {
      location: {origin},
      addEventListener: (type, fn) => listeners.set(type, fn),
      skipWaiting: async () => {},
      clients: {claim: async () => {}}
    }
  };
  vm.runInNewContext(readFileSync('service-worker.js', 'utf8'), sandbox);
  let pending;
  listeners.get('fetch')({
    request: {method: 'GET', url: origin + pathname, mode: 'no-cors', destination, headers: new Headers()},
    respondWith(promise) { pending = promise; },
    waitUntil() {}
  });
  assert.ok(pending, `${pathname}: petición no gestionada`);
  const response = await pending.catch(error => {
    assert.fail(`${pathname}: error de almacenamiento propagado: ${error.message}`);
  });
  assert.equal(response.status, 200, `${pathname}: estado HTTP incorrecto`);
  assert.deepEqual(new Uint8Array(await response.arrayBuffer()), payload, `${pathname}: bytes alterados`);
  assert.equal(calls, 1, `${pathname}: peticiones duplicadas o ausentes (${calls})`);
}
console.log('PASS image and font network request cardinality');