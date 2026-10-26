import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const origin = 'https://davidportodiaz.com';
const resources = [
  ['/assets/v1-base.css', 'text/css', 'body{color:black}'],
  ['/assets/v1-fragments.js', 'text/javascript', 'export const ready=true;'],
  ['/assets/editorial-public-facts.mjs', 'text/javascript', 'export const facts={};']
];

for (const [pathname, mime, body] of resources) {
  const listeners = new Map();
  let networkCalls = 0;
  const sandbox = {
    URL, Request, Response, Headers, console,
    caches: {
      open: async () => { throw new Error('CacheStorage unavailable'); },
      keys: async () => [],
      delete: async () => true
    },
    fetch: async () => {
      networkCalls++;
      return new Response(body, {status: 200, headers: {'Content-Type': mime}});
    },
    self: {
      location: {origin},
      addEventListener: (type, listener) => listeners.set(type, listener),
      skipWaiting: async () => {},
      clients: {claim: async () => {}}
    }
  };
  vm.runInNewContext(readFileSync('service-worker.js', 'utf8'), sandbox);
  let pending;
  listeners.get('fetch')({
    request: {
      method: 'GET', url: origin + pathname,
      mode: 'cors', destination: pathname.endsWith('.css') ? 'style' : 'script',
      headers: new Headers()
    },
    respondWith(value) { pending = value; },
    waitUntil() {}
  });
  assert.ok(pending, `${pathname}: el SW no gestionó el recurso`);
  const response = await pending.catch(error => {
    assert.fail(`${pathname}: CacheStorage impidió cargar el recurso: ${error.message}`);
  });
  assert.equal(response.status, 200, `${pathname}: HTTP incorrecto`);
  assert.equal(await response.text(), body, `${pathname}: contenido perdido`);
  assert.equal(networkCalls, 1, `${pathname}: número de peticiones de red incorrecto`);
}
console.log('PASS static resources survive CacheStorage failure');