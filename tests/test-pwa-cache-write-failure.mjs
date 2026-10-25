import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const listeners = new Map();
const warnings = [];
let attempts = 0;
const cache = {
  match: async () => null,
  put: async () => {
    attempts++;
    throw new Error('QuotaExceededError');
  }
};
const sandbox = {
  URL, Request, Response, Headers,
  console: { warn: (...args) => warnings.push(args) },
  caches: { open: async () => cache },
  fetch: async () => new Response('VALID_NETWORK_BODY', { status: 200 }),
  self: {
    location: { origin: 'https://davidportodiaz.com' },
    addEventListener: (name, handler) => listeners.set(name, handler)
  }
};
vm.runInNewContext(fs.readFileSync('service-worker.js', 'utf8'), sandbox);
const handler = listeners.get('fetch');

for (const [path, mode] of [
  ['/__qa_quota/', 'navigate'],
  ['/assets/__qa_quota.js', 'cors'],
  ['/assets/__qa_quota.png', 'cors']
]) {
  let promise;
  const waits = [];
  handler({
    request: {
      method: 'GET',
      url: `https://davidportodiaz.com${path}`,
      mode,
      destination: mode === 'navigate' ? 'document' : '',
      headers: new Headers()
    },
    respondWith: value => { promise = Promise.resolve(value); },
    waitUntil: value => waits.push(Promise.resolve(value))
  });
  assert.ok(promise, `No response for ${path}`);
  const response = await promise;
  await Promise.all(waits);
  assert.equal(response.status, 200);
  assert.equal(await response.text(), 'VALID_NETWORK_BODY');
}
assert.equal(attempts, 3);
assert.equal(warnings.length, 3);
console.log('PASS: CacheStorage write failures preserve network responses');