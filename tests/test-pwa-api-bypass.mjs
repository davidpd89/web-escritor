import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync('service-worker.js', 'utf8');
const listeners = new Map();
const sandbox = {
  URL,
  Request,
  Response,
  console,
  caches: {
    open: async () => ({ match: async () => null, put: async () => undefined, addAll: async () => undefined }),
    keys: async () => [],
    delete: async () => true,
  },
  fetch: async () => new Response('ok', { status: 200 }),
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

function dispatch(path, mode = 'cors') {
  let responded = false;
  const event = {
    request: { method: 'GET', url: `https://davidportodiaz.com${path}`, mode },
    respondWith() { responded = true; },
    waitUntil() {},
  };
  fetchHandler(event);
  return responded;
}

for (const path of ['/api', '/api/', '/api/assistant', '/api/assistant/config', '/api/future-endpoint?x=1']) {
  assert.equal(dispatch(path), false, `${path} must bypass the service worker cache completely`);
}
assert.equal(dispatch('/assets/icon-512.png'), true, 'normal same-origin assets must remain service-worker owned');
assert.equal(dispatch('/humans.txt'), true, 'normal same-origin public GET must retain the existing strategy');

const apiGuard = source.indexOf('url.pathname === "/api" || url.pathname.startsWith("/api/")');
const navigateBranch = source.indexOf('request.mode === "navigate"');
assert(apiGuard >= 0 && navigateBranch >= 0 && apiGuard < navigateBranch, 'API bypass must run before navigation/static/cache strategies');

console.log('PASS: service worker bypasses all same-origin /api endpoints');
