import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const origin = 'https://davidportodiaz.com';
const listeners = new Map();
const operations = [];
const cache = {
  match: async () => {
    operations.push('cache-read');
    return new Response('export const purchaseUrl = null;', {headers: {'Content-Type': 'text/javascript'}});
  },
  put: async (request, response) => {
    operations.push('cache-write');
    assert.match(await response.text(), /https:\/\/amzn\.to\//, request.url + ': copia nueva incorrecta');
  }
};
const sandbox = {
  URL, Request, Response, Headers, Promise, Set, console,
  caches: {open: async () => cache},
  fetch: async () => {
    operations.push('network');
    return new Response('export const purchaseUrl = "https://amzn.to/4zW6Yeu";', {
      status: 200,
      headers: {'Content-Type': 'text/javascript'}
    });
  },
  self: {
    location: {origin},
    addEventListener: (type, callback) => listeners.set(type, callback)
  }
};
vm.runInNewContext(readFileSync('service-worker.js', 'utf8'), sandbox);
let pending;
listeners.get('fetch')({
  request: new Request(origin + '/assets/editorial-public-facts.mjs'),
  respondWith: value => {pending = Promise.resolve(value);},
  waitUntil() {}
});
assert.ok(pending, 'editorial-public-facts.mjs: no se interceptó la solicitud');
const response = await pending;
assert.match(await response.text(), /https:\/\/amzn\.to\/4zW6Yeu/, 'editorial-public-facts.mjs: se devolvió el enlace antiguo');
assert.deepEqual(operations, ['network', 'cache-write'], 'editorial-public-facts.mjs: se consultó la caché antes que la red');
console.log('PASS: editorial module network-first');