import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync('service-worker.js', 'utf8');
const offline = fs.readFileSync('offline.html', 'utf8');
const handlers = {};
const cache = {
  match: async request => {
    const url = typeof request === 'string' ? request : request.url;
    return url === '/offline.html'
      ? new Response(offline, { status: 200, headers: { 'Content-Type': 'text/html' } })
      : undefined;
  },
  put: async () => {}
};
const context = {
  URL, Request, Response, Set, Promise, console,
  fetch: async () => { throw new TypeError('Network unavailable'); },
  caches: { open: async () => cache },
  self: {
    location: { origin: 'https://davidportodiaz.com' },
    addEventListener: (name, handler) => { handlers[name] = handler; }
  }
};
vm.createContext(context);
vm.runInContext(source, context, { filename: 'service-worker.js' });
assert.equal(typeof handlers.fetch, 'function');
const request = {
  url: 'https://davidportodiaz.com/herramientas/json-ld-escritores/',
  method: 'GET', mode: 'navigate', cache: 'default',
  headers: new Headers(), destination: 'document'
};
let responsePromise;
handlers.fetch({ request, respondWith: value => { responsePromise = Promise.resolve(value); } });
assert.ok(responsePromise, `${request.url}: navegación sin respuesta del Service Worker`);
const response = await responsePromise;
assert.equal(response.status, 200, `${request.url}: fallback HTTP incorrecto`);
const html = await response.text();
assert.match(html, /data-retry/, `${request.url}: falta acción de reintento offline`);
assert.match(html, /data-status/, `${request.url}: falta estado accesible offline`);
assert.match(html, /<main\b/i, `${request.url}: fallback sin contenido principal`);
console.log('PWA: recuperación de navegación offline correcta');
