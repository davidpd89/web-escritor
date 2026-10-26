import assert from 'node:assert/strict';
import vm from 'node:vm';
import { readFileSync } from 'node:fs';

const source = readFileSync('service-worker.js', 'utf8');
const version = source.match(/const CACHE_VERSION = `\$\{CACHE_NAMESPACE\}-(v\d+)`/);
assert.ok(version, 'service-worker.js: no se pudo identificar la versión actual');
const current = 'david-porto-pwa-' + version[1];
const initial = [
  current + '-static',
  current + '-pages',
  'david-porto-pwa-v14-static',
  'david-porto-pwa-v15-pages',
  'david-porto-pwa-v1-static',
  'other-application-cache',
  'pagefind-private-cache'
];
const remaining = new Set(initial);
const deleted = [];
const handlers = {};
let claimed = false;
const self = {
  addEventListener: (name, callback) => { handlers[name] = callback; },
  clients: { claim: async () => { claimed = true; } }
};
vm.runInNewContext(source, {
  self, URL, Request, Response, Headers, console,
  caches: {
    keys: async () => [...remaining],
    delete: async key => {
      deleted.push(key);
      return remaining.delete(key);
    }
  }
});
let activation;
handlers.activate({ waitUntil: promise => { activation = promise; } });
assert.ok(activation, 'service-worker.js: activate no registró waitUntil');
await activation;
for (const key of [current + '-static', current + '-pages', 'other-application-cache', 'pagefind-private-cache']) {
  assert.ok(remaining.has(key), `CacheStorage: se eliminó indebidamente ${key}`);
}
for (const key of ['david-porto-pwa-v14-static', 'david-porto-pwa-v15-pages', 'david-porto-pwa-v1-static']) {
  assert.ok(!remaining.has(key), `CacheStorage: permanece la caché obsoleta ${key}`);
}
assert.ok(claimed, 'service-worker.js: no reclamó los clientes tras activar');
assert.equal(deleted.length, new Set(deleted).size, 'CacheStorage: eliminaciones duplicadas');
console.log('PASS PWA cache namespace isolation');