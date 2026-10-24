import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync(new URL('../service-worker.js', import.meta.url), 'utf8');

async function probe(headers, pathname) {
  const listeners = new Map();
  const writes = [];
  const cache = {
    match: async () => null,
    put: async (request, response) => { writes.push({ request, response }); },
    addAll: async () => undefined,
  };
  const sandbox = {
    URL, Request, Response, Headers, console,
    caches: {
      open: async () => cache,
      keys: async () => [],
      delete: async () => true,
    },
    fetch: async () => new Response('contenido privado', { status: 200, headers }),
    self: {
      location: { origin: 'https://davidportodiaz.com' },
      addEventListener: (name, fn) => listeners.set(name, fn),
      skipWaiting: async () => undefined,
      clients: { claim: async () => undefined },
    },
  };
  vm.createContext(sandbox);
  vm.runInContext(source, sandbox, { filename: 'service-worker.js' });
  let pending;
  listeners.get('fetch')({
    request: {
      method: 'GET',
      url: 'https://davidportodiaz.com' + pathname,
      mode: 'navigate',
      destination: 'document',
      headers: new Headers(),
    },
    respondWith: p => { pending = p; },
    waitUntil: () => undefined,
  });
  assert.ok(pending, pathname + ': navegación no interceptada');
  await pending;
  assert.equal(writes.length, 0, pathname + ': respuesta privada almacenada');
}

for (const [headers, path] of [
  [{ 'Cache-Control': 'private' }, '/cuaderno/'],
  [{ 'Cache-Control': 'no-store' }, '/recomendaciones/'],
  [{ 'Set-Cookie': 'session=qa; HttpOnly; Secure' }, '/asistente/'],
]) {
  await probe(headers, path);
}
console.log('PASS Service Worker: las respuestas privadas no entran en CacheStorage');
