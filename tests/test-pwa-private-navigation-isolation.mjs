import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const handlers = {};
let cacheAccess = 0;
let networkCalls = 0;
let failNetwork = false;
const context = {
  URL, Request, Response, Set, Headers, console,
  self: {
    location: { origin: 'https://davidportodiaz.com' },
    addEventListener(type, callback) { handlers[type] = callback; }
  },
  caches: {
    async open() { cacheAccess++; throw Error('Authenticated navigation accessed shared cache'); }
  },
  async fetch() {
    networkCalls++;
    if (failNetwork) throw Error('Network unavailable');
    return new Response('<h1>Respuesta de red</h1>', { status: 200, headers: { 'Content-Type': 'text/html' } });
  }
};
vm.createContext(context);
vm.runInContext(fs.readFileSync('service-worker.js', 'utf8'), context);
async function navigate() {
  let responsePromise;
  handlers.fetch({
    request: {
      url: 'https://davidportodiaz.com/asistente/',
      method: 'GET',
      mode: 'navigate',
      destination: 'document',
      cache: 'default',
      headers: new Headers({ Authorization: 'Bearer test' })
    },
    respondWith(value) { responsePromise = Promise.resolve(value); },
    waitUntil() {}
  });
  assert.ok(responsePromise, '/asistente/: navegación autenticada sin respuesta controlada');
  return responsePromise;
}
let response = await navigate();
assert.equal(response.status, 200, '/asistente/: navegación autenticada online debe conservar la respuesta');
assert.match(await response.text(), /Respuesta de red/);
failNetwork = true;
response = await navigate();
assert.equal(response.status, 504, '/asistente/: navegación autenticada offline no debe recuperar HTML compartido');
assert.equal(cacheAccess, 0, '/asistente/: navegación autenticada accedió a CacheStorage');
assert.equal(networkCalls, 2, '/asistente/: número incorrecto de solicitudes de red');
console.log('PASS: navegación autenticada aislada de CacheStorage');