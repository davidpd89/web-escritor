import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const code = fs.readFileSync('service-worker.js', 'utf8');
const handlers = new Map();
const writes = [];
let response = null;
const cache = {
  put: async (request, value) => writes.push({url: request.url, type: value.headers.get('content-type')}),
  match: async () => undefined,
};
const sandbox = {
  self: {
    location: {origin: 'https://local.invalid'},
    addEventListener: (name, fn) => handlers.set(name, fn),
  },
  caches: {
    open: async () => cache,
    keys: async () => [],
    delete: async () => true,
  },
  fetch: async () => response.clone(),
  Request, Response, URL, Set, Promise,
};
vm.runInNewContext(code, sandbox, {filename: 'service-worker.js'});
assert.ok(handlers.has('fetch'));

async function dispatch(url) {
  let promise;
  const request = new Request(url);
  handlers.get('fetch')({
    request,
    respondWith: value => { promise = Promise.resolve(value); },
    waitUntil: () => {},
  });
  assert.ok(promise, `El SW no interceptó ${url}`);
  return promise;
}

response = new Response('<!doctype html><title>Error</title>', {
  status: 200,
  headers: {'content-type': 'text/html; charset=utf-8'},
});
await dispatch('https://local.invalid/assets/assistant.js');
assert.equal(writes.length, 0, 'El SW almacenó HTML como JavaScript válido');

response = new Response('export const value = 1;', {
  status: 200,
  headers: {'content-type': 'text/javascript; charset=utf-8'},
});
await dispatch('https://local.invalid/assets/assistant.js');
assert.equal(writes.length, 1, 'El SW dejó de cachear JavaScript legítimo');
assert.equal(writes[0].url, 'https://local.invalid/assets/assistant.js');
console.log('PASS: Service Worker MIME poisoning');
