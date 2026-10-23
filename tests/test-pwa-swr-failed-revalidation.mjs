import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const listeners = new Map();
let failureMode = 'http';
let writes = 0;
const cache = {
  match: async () => new Response('KNOWN-GOOD-IMAGE', { status: 200 }),
  put: async () => { writes++; },
  addAll: async () => {}
};
const sandbox = {
  URL, Request, Response, Headers, console,
  caches: { open: async () => cache, keys: async () => [], delete: async () => true },
  fetch: async () => {
    if (failureMode === 'network') throw new TypeError('Connection reset');
    return new Response('BROKEN-IMAGE', { status: 500 });
  },
  self: {
    location: { origin: 'https://davidportodiaz.com' },
    addEventListener: (type, fn) => listeners.set(type, fn),
    skipWaiting: async () => {},
    clients: { claim: async () => {} }
  }
};
vm.runInNewContext(fs.readFileSync('service-worker.js', 'utf8'), sandbox);
for (const mode of ['http', 'network']) {
  failureMode = mode;
  let responsePromise;
  const background = [];
  listeners.get('fetch')({
    request: {
      method: 'GET', url: 'https://davidportodiaz.com/assets/cover.webp',
      mode: 'cors', destination: 'image', headers: new Headers()
    },
    respondWith: p => { responsePromise = p; },
    waitUntil: p => background.push(p)
  });
  assert.ok(responsePromise);
  const response = await responsePromise;
  assert.equal(response.status, 200);
  assert.equal(await response.text(), 'KNOWN-GOOD-IMAGE');
  assert.equal(background.length, 1, `${mode}: la revalidación no fue registrada`);
  await Promise.all(background);
  assert.equal(writes, 0, `${mode}: un resultado fallido sobrescribió la caché`);
}
console.log('PASS: SWR conserva contenido válido ante HTTP 500 y desconexión');