import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync('service-worker.js', 'utf8');
const version = source.match(/CACHE_NAMESPACE\}-v(\d+)/)?.[1];
assert.ok(version);
const current = `david-porto-pwa-v${version}`;
const names = [current + '-static', current + '-pages', 'david-porto-pwa-v13-static', 'external-cache'];
const listeners = new Map();
const deleted = [];
let claimed = false;
let unlock;
const gate = new Promise(resolve => { unlock = resolve; });
const sandbox = {
  URL, Request, Response, Headers, console,
  caches: {
    keys: async () => [...names],
    open: async () => ({}),
    delete: async name => { deleted.push(name); await gate; return true; }
  },
  self: {
    location: { origin: 'https://davidportodiaz.com' },
    addEventListener: (type, fn) => listeners.set(type, fn),
    skipWaiting: async () => {},
    clients: { claim: async () => { claimed = true; } }
  }
};
vm.runInNewContext(source, sandbox);
let pending;
listeners.get('activate')({ waitUntil: promise => { pending = promise; } });
assert.ok(pending);
await new Promise(resolve => setImmediate(resolve));
assert.equal(claimed, false, 'Se reclamó el control antes de terminar la limpieza');
assert.deepEqual(deleted, ['david-porto-pwa-v13-static']);
unlock();
await pending;
assert.equal(claimed, true, 'El control nunca fue reclamado');
assert.ok(!deleted.includes('external-cache'));
assert.ok(!deleted.includes(current + '-static'));
assert.ok(!deleted.includes(current + '-pages'));
console.log('PASS: activación espera a la eliminación de cachés obsoletas');