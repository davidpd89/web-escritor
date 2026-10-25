import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const listeners = new Map();
let status = 200;
let writes = 0;
const cache = {
  match: async () => new Response('OLD_VALID_CONTENT', { status: 200 }),
  put: async () => { writes++; }
};
const sandbox = {
  URL, Request, Response, Headers, console,
  caches: { open: async () => cache },
  fetch: async () => new Response('SERVER_ERROR_BODY', { status }),
  self: {
    location: { origin: 'https://davidportodiaz.com' },
    addEventListener: (name, callback) => listeners.set(name, callback)
  }
};
vm.runInNewContext(fs.readFileSync('service-worker.js', 'utf8'), sandbox);
const handler = listeners.get('fetch');

for (const code of [404, 429, 503]) {
  status = code;
  writes = 0;
  let promise;
  handler({
    request: {
      method: 'GET',
      url: 'https://davidportodiaz.com/assets/__qa_http_error.js',
      mode: 'cors',
      destination: 'script',
      headers: new Headers()
    },
    respondWith: value => { promise = Promise.resolve(value); },
    waitUntil: () => {}
  });
  assert.ok(promise);
  const response = await promise;
  assert.equal(response.status, code);
  assert.equal(await response.text(), 'SERVER_ERROR_BODY');
  assert.equal(writes, 0, `HTTP ${code} overwrote cached success`);
}
console.log('PASS: HTTP errors preserve status and existing cache');