import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const origin = 'https://davidportodiaz.com';
const listeners = new Map();
const writes = [];
const cache = {
  match: async () => undefined,
  put: async request => writes.push(request.url)
};
const sandbox = {
  URL, Request, Response, Headers, Promise, Set, console,
  caches: {open: async () => cache},
  fetch: async () => new Response('parte', {
    status: 206,
    headers: {
      'Content-Type': 'text/javascript',
      'Content-Range': 'bytes 0-4/20'
    }
  }),
  self: {
    location: {origin},
    addEventListener: (type, callback) => listeners.set(type, callback)
  }
};
vm.runInNewContext(readFileSync('service-worker.js', 'utf8'), sandbox);
let pending;
listeners.get('fetch')({
  request: new Request(origin + '/script.js'),
  respondWith: value => {pending = Promise.resolve(value);},
  waitUntil() {}
});
assert.ok(pending, '/script.js: solicitud no gestionada');
const response = await pending;
assert.equal(response.status, 206, '/script.js: se perdió el estado parcial');
assert.equal(response.headers.get('Content-Range'), 'bytes 0-4/20', '/script.js: se perdió Content-Range');
assert.equal(await response.text(), 'parte', '/script.js: cuerpo parcial modificado');
assert.deepEqual(writes, [], '/script.js: se almacenó una respuesta parcial');
console.log('PASS: SW partial response integrity');