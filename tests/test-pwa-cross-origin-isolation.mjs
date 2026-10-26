import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const handlers = {};
let cacheCalls = 0;
let networkCalls = 0;
const origin = 'https://davidportodiaz.com';
const context = {
  URL, Request, Response, Set, console,
  self: {
    location: { origin },
    addEventListener(type, callback) { handlers[type] = callback; }
  },
  caches: {
    async open() { cacheCalls++; throw Error('External request entered CacheStorage'); }
  },
  async fetch() { networkCalls++; throw Error('External request intercepted'); }
};
vm.createContext(context);
vm.runInContext(fs.readFileSync('service-worker.js', 'utf8'), context, { filename: 'service-worker.js' });
assert.equal(typeof handlers.fetch, 'function', 'service-worker.js: falta el controlador fetch');
for (const url of [
  'https://gc.zgo.at/count.js',
  'https://tracker.metricool.com/c3po.js',
  'https://subscribe.davidpd89.workers.dev/'
]) {
  let intercepted = false;
  handlers.fetch({
    request: {
      url,
      method: 'GET',
      mode: 'cors',
      destination: 'script',
      cache: 'default',
      headers: new Headers()
    },
    respondWith() { intercepted = true; },
    waitUntil() { intercepted = true; }
  });
  assert.equal(intercepted, false, `${url}: el service worker intercepta un recurso externo`);
}
assert.equal(cacheCalls, 0, 'service-worker.js: solicitudes externas accedieron a CacheStorage');
assert.equal(networkCalls, 0, 'service-worker.js: solicitudes externas pasaron por fetch del worker');
console.log('PASS: aislamiento de solicitudes externas de la PWA');