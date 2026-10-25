import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const listeners = new Map();
let networkCalls = 0;
let releaseNetwork;
const gate = new Promise(resolve => { releaseNetwork = resolve; });
const cache = {
  match: async () => null,
  put: async () => {}
};
const sandbox = {
  URL, Request, Response, Headers, console,
  caches: { open: async () => cache },
  fetch: async () => {
    networkCalls++;
    await gate;
    return new Response('SHARED_RESOURCE', { status: 200 });
  },
  self: {
    location: { origin: 'https://davidportodiaz.com' },
    addEventListener: (name, callback) => listeners.set(name, callback)
  }
};
vm.runInNewContext(fs.readFileSync('service-worker.js', 'utf8'), sandbox);
const handler = listeners.get('fetch');
const promises = [];
for (let i = 0; i < 8; i++) {
  handler({
    request: {
      method: 'GET',
      url: 'https://davidportodiaz.com/assets/__qa_shared.js',
      mode: 'cors',
      destination: 'script',
      headers: new Headers()
    },
    respondWith: promise => promises.push(Promise.resolve(promise)),
    waitUntil: () => {}
  });
}
assert.equal(promises.length, 8);
releaseNetwork();
const responses = await Promise.all(promises);
for (const response of responses) {
  assert.equal(response.status, 200);
  assert.equal(await response.text(), 'SHARED_RESOURCE');
}
assert.equal(networkCalls, 1, `Expected one coalesced request, received ${networkCalls}`);
console.log('PASS: concurrent identical requests deduplicated');