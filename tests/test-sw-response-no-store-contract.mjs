import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const handlers = new Map();
const writes = [];
const origin = 'https://davidportodiaz.com';
const cache = {
  put: async (request) => writes.push(request.url),
  match: async () => undefined
};
const sandbox = {
  URL, Request, Response, Headers, Promise, Set, console,
  caches: {open: async () => cache},
  fetch: async () => new Response('export const version = 17;', {
    status: 200,
    headers: {
      'Content-Type': 'text/javascript',
      'Cache-Control': 'public, max-age=0, no-store'
    }
  }),
  self: {
    location: {origin},
    addEventListener: (type, callback) => handlers.set(type, callback)
  }
};
vm.runInNewContext(readFileSync('service-worker.js', 'utf8'), sandbox, {filename: 'service-worker.js'});
const request = new Request(origin + '/assets/editorial-public-facts.mjs');
let pending;
handlers.get('fetch')({
  request,
  respondWith: value => {pending = Promise.resolve(value);},
  waitUntil() {}
});
assert.ok(pending, 'editorial-public-facts.mjs: petición sin respuesta del SW');
const response = await pending;
assert.equal(response.status, 200, 'editorial-public-facts.mjs: estado HTTP alterado');
assert.match(await response.text(), /version = 17/, 'editorial-public-facts.mjs: contenido alterado');
assert.deepEqual(writes, [], 'editorial-public-facts.mjs: se almacenó una respuesta con no-store');
console.log('PASS: SW response no-store contract');