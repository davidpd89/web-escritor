// Regression for a latent risk flagged after #388 (2026-09-05): #388 made
// .mjs network-first in the fetch handler, closing the staleness bug while
// online, but a visitor who cached editorial-public-facts.mjs's old
// purchaseUrl:null into v14's STATIC_CACHE before #388, then went offline
// without ever re-fetching it online again, could still have been served
// that stale copy as the offline fallback -- v14's cache name never changed,
// so nothing forced that old entry out. Bumping CACHE_VERSION to v15 and
// listing v14's cache names in LEGACY_PWA_CACHES makes the `activate`
// handler purge them outright instead of leaving that window open
// indefinitely. This drives the real service worker in a sandbox and proves
// the purge actually happens, without touching unrelated caches on the origin.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync('service-worker.js', 'utf8');
const listeners = new Map();
const existingCaches = new Set([
  'david-porto-pwa-v14-static',
  'david-porto-pwa-v14-pages',
  'david-porto-v2026-08-20-launch-1-static',
  'some-totally-unrelated-cache-on-this-origin',
]);
const deleted = [];
const sandbox = {
  URL, Request, Response, console,
  caches: {
    open: async (name) => { existingCaches.add(name); return { match: async () => null, put: async () => undefined, addAll: async () => undefined }; },
    keys: async () => Array.from(existingCaches),
    delete: async (name) => { deleted.push(name); existingCaches.delete(name); return true; },
  },
  self: {
    location: { origin: 'https://davidportodiaz.com' },
    addEventListener(type, handler) { listeners.set(type, handler); },
    skipWaiting: async () => undefined,
    clients: { claim: async () => undefined },
  },
};
vm.createContext(sandbox);
vm.runInContext(source, sandbox, { filename: 'service-worker.js' });

const activateHandler = listeners.get('activate');
assert.equal(typeof activateHandler, 'function', 'activate handler missing');
let waited;
activateHandler({ waitUntil: (p) => { waited = p; } });
await waited;

assert.ok(deleted.includes('david-porto-pwa-v14-static'), 'v14 static cache (potential stale .mjs) must be purged on activation');
assert.ok(deleted.includes('david-porto-pwa-v14-pages'), 'v14 page cache must be purged on activation');
assert.ok(deleted.includes('david-porto-v2026-08-20-launch-1-static'), 'ancient legacy cache must still be purged');
assert.ok(!deleted.includes('some-totally-unrelated-cache-on-this-origin'), 'unrelated caches on the origin must never be touched');

const version = source.match(/const CACHE_VERSION = `\$\{CACHE_NAMESPACE\}-(v\d+)`;/)?.[1];
assert.ok(version, 'CACHE_VERSION declaration missing');
assert.ok(Number(version.slice(1)) >= 15, 'cache must be bumped past v14 to purge any stale-.mjs entries cached before #388');

console.log(`PASS: stale v14 cache (${version} now current) is purged on activation, unrelated caches untouched`);
