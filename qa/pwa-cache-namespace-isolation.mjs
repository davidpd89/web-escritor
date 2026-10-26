import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync('service-worker.js', 'utf8');
const existing = new Set([
  'david-porto-pwa-v16-static',
  'david-porto-pwa-v17-static',
  'david-porto-pwa-v17-pages',
  'unrelated-application-cache'
]);
const removed = [];
const handlers = {};
const context = {
  URL, Request, Response, Set, Promise,
  console,
  caches: {
    keys: async () => [...existing],
    delete: async key => { removed.push(key); existing.delete(key); return true; }
  },
  self: {
    location: { origin: 'https://davidportodiaz.com' },
    clients: { claim: async () => {} },
    addEventListener: (name, handler) => { handlers[name] = handler; }
  }
};
vm.createContext(context);
vm.runInContext(source, context, { filename: 'service-worker.js' });
assert.equal(typeof handlers.activate, 'function', 'service-worker.js: falta el evento activate');
let activation;
handlers.activate({ waitUntil: promise => { activation = promise; } });
assert.ok(activation, 'service-worker.js: activate no espera la limpieza');
await activation;
assert.ok(existing.has('unrelated-application-cache'), 'activate: se ha eliminado una caché ajena');
assert.ok(existing.has('david-porto-pwa-v17-static'), 'activate: se ha eliminado la caché estática actual');
assert.ok(existing.has('david-porto-pwa-v17-pages'), 'activate: se ha eliminado la caché de páginas actual');
assert.ok(!existing.has('david-porto-pwa-v16-static'), 'activate: permanece una caché obsoleta propia');
assert.ok(!removed.includes('unrelated-application-cache'), 'activate: intento de eliminar caché ajena');
console.log('PWA: aislamiento de cachés correcto');
