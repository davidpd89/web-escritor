import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync('service-worker.js', 'utf8');
const listeners = new Map();
const stores = new Map();
const origin = 'https://davidportodiaz.com';
const version = source.match(/CACHE_NAMESPACE\}-v(\d+)/)?.[1];
assert.ok(version);
const pageCache = `david-porto-pwa-v${version}-pages`;
const staticCache = `david-porto-pwa-v${version}-static`;
const sandbox = {
  URL, Request, Response, Headers, console,
  caches: {
    open: async name => {
      if (!stores.has(name)) stores.set(name, new Map());
      const entries = stores.get(name);
      return {
        match: async request => entries.get(request.url || request)?.clone() || null,
        put: async (request, response) => entries.set(request.url || request, response.clone())
      };
    },
    keys: async () => [...stores.keys()], delete: async name => stores.delete(name)
  },
  fetch: async () => { throw new TypeError('Offline'); },
  self: {
    location: { origin },
    addEventListener: (type, fn) => listeners.set(type, fn),
    skipWaiting: async () => {}, clients: { claim: async () => {} }
  }
};
vm.runInNewContext(source, sandbox);
await (await sandbox.caches.open(pageCache)).put({ url: origin + '/cuaderno/?version=1' }, new Response('CACHED-ARTICLE-ONE'));
await (await sandbox.caches.open(staticCache)).put('/offline.html', new Response('OFFLINE-FALLBACK'));
async function navigate(path) {
  let promise;
  listeners.get('fetch')({
    request: { method: 'GET', url: origin + path, mode: 'navigate', destination: 'document', headers: new Headers() },
    respondWith: p => { promise = p; }, waitUntil: () => {}
  });
  assert.ok(promise);
  return (await promise).text();
}
assert.equal(await navigate('/cuaderno/?version=1'), 'CACHED-ARTICLE-ONE');
for (const path of ['/cuaderno/?version=2', '/libros/', '/herramientas/']) {
  assert.equal(await navigate(path), 'OFFLINE-FALLBACK', path);
}
console.log('PASS: aislamiento offline por ruta y parámetros de navegación');