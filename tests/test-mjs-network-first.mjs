// Regression for a real bug (reproduced live 2026-09-04): assets/*.mjs files
// (editorial-public-facts.mjs, assistant-*.mjs) fell through the service
// worker's /assets/ stale-while-revalidate branch instead of the .css/.js
// network-first branch. editorial-public-facts.mjs had shipped with
// purchaseUrl: null before #384 set Las manecillas del recuerdo's real
// Kindle link -- a visitor whose browser had cached that null-value response
// got served it again (stale) the first time #387's module-based Home CTAs
// ran, rendering href="null" (a literal "/null" link on "Comprar",
// "Comprar en Amazon", etc). This drives the actual service-worker.js fetch
// handler in a sandbox and proves .mjs now behaves like .js: the network
// response wins even when a stale cached response exists, unlike a real
// /assets/ image which must keep serving stale-while-revalidate.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync('service-worker.js', 'utf8');
const listeners = new Map();

function makeCache(staleBody) {
  const puts = [];
  return {
    match: async () => (staleBody ? new Response(staleBody, { status: 200 }) : null),
    put: async (request, response) => { puts.push({ request, response }); },
    addAll: async () => undefined,
    _puts: puts,
  };
}

const caches_ = new Map();
const sandbox = {
  URL,
  Request,
  Response,
  Headers,
  console,
  caches: {
    open: async (name) => {
      if (!caches_.has(name)) caches_.set(name, makeCache('STALE-CACHED-BODY'));
      return caches_.get(name);
    },
    keys: async () => [],
    delete: async () => true,
  },
  fetch: async () => new Response('FRESH-NETWORK-BODY', { status: 200 }),
  self: {
    location: { origin: 'https://davidportodiaz.com' },
    addEventListener(type, handler) { listeners.set(type, handler); },
    skipWaiting: async () => undefined,
    clients: { claim: async () => undefined },
  },
};
vm.createContext(sandbox);
vm.runInContext(source, sandbox, { filename: 'service-worker.js' });

const fetchHandler = listeners.get('fetch');
assert.equal(typeof fetchHandler, 'function', 'service worker fetch handler missing');

async function dispatchAndRead(path) {
  let waitUntilCalled = false;
  let responsePromise = null;
  const event = {
    request: { method: 'GET', url: `https://davidportodiaz.com${path}`, mode: 'cors', headers: new Headers(), destination: '' },
    respondWith(p) { responsePromise = p; },
    waitUntil() { waitUntilCalled = true; },
  };
  fetchHandler(event);
  assert.ok(responsePromise, `${path}: respondWith was never called`);
  const response = await responsePromise;
  const body = await response.text();
  return { body, waitUntilCalled };
}

// The bug: an .mjs module must win with the network's fresh response even
// though a stale cached response exists -- exactly like .js already does.
for (const path of ['/assets/editorial-public-facts.mjs', '/assets/assistant-local-knowledge.mjs', '/assets/v1-home-editorial-v3.js']) {
  const { body, waitUntilCalled } = await dispatchAndRead(path);
  assert.equal(body, 'FRESH-NETWORK-BODY', `${path}: must be network-first (got stale cached body instead)`);
  assert.equal(waitUntilCalled, false, `${path}: network-first strategy must not use waitUntil (that is stale-while-revalidate's signature)`);
}

// Sanity check the fix didn't overreach: a real /assets/ image must keep
// stale-while-revalidate (serve cached immediately, revalidate in background).
const image = await dispatchAndRead('/assets/icon-512.png');
assert.equal(image.body, 'STALE-CACHED-BODY', '/assets/icon-512.png: must still serve stale-while-revalidate, not network-first');
assert.equal(image.waitUntilCalled, true, '/assets/icon-512.png: stale-while-revalidate must background-revalidate via waitUntil');

console.log('PASS: .mjs modules under /assets/ are network-first, same as .css/.js; other /assets/ stay stale-while-revalidate');
