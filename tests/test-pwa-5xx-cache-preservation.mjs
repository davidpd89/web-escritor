import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const listeners = new Map();
const stores = new Map();
let offline = false;
let attemptedWrites = 0;
const sandbox = {
  URL, Request, Response, Headers, console,
  caches: {
    open: async name => {
      if (!stores.has(name)) stores.set(name, new Map());
      const entries = stores.get(name);
      return {
        match: async req => entries.get(req.url || req)?.clone() || null,
        put: async (req, response) => {
          attemptedWrites++;
          entries.set(req.url || req, response.clone());
        },
        addAll: async () => {}
      };
    },
    keys: async () => [...stores.keys()],
    delete: async name => stores.delete(name)
  },
  fetch: async () => {
    if (offline) throw new TypeError('Network unavailable');
    return new Response('SERVER-DOWN', { status: 503 });
  },
  self: {
    location: { origin: 'https://davidportodiaz.com' },
    addEventListener: (type, fn) => listeners.set(type, fn),
    skipWaiting: async () => {},
    clients: { claim: async () => {} }
  }
};
const source = fs.readFileSync('service-worker.js', 'utf8');
vm.runInNewContext(source, sandbox);
const version = source.match(/david-porto-pwa.*?-v(\d+)/)?.[1];
assert.ok(version);
async function dispatch(path, mode) {
  let promise;
  listeners.get('fetch')({
    request: { method: 'GET', url: 'https://davidportodiaz.com' + path, mode, destination: '', headers: new Headers() },
    respondWith: p => { promise = p; }, waitUntil: () => {}
  });
  assert.ok(promise);
  return promise;
}
for (const [path, mode, suffix] of [
  ['/cuaderno/?qa=503', 'navigate', 'pages'],
  ['/assets/regression.mjs', 'cors', 'static']
]) {
  const name = `david-porto-pwa-v${version}-${suffix}`;
  const cache = await sandbox.caches.open(name);
  const url = 'https://davidportodiaz.com' + path;
  await cache.put({ url }, new Response('LAST-GOOD-VERSION', { status: 200 }));
  const before = attemptedWrites;
  const online = await dispatch(path, mode);
  assert.equal(online.status, 503);
  assert.equal(attemptedWrites, before, `${path}: se intentó guardar un 503`);
  assert.equal(await (await cache.match({ url })).text(), 'LAST-GOOD-VERSION');
  offline = true;
  const recovered = await dispatch(path, mode);
  assert.equal(recovered.status, 200);
  assert.equal(await recovered.text(), 'LAST-GOOD-VERSION');
  offline = false;
}
console.log('PASS: errores 503 no contaminan cachés de documentos ni módulos');