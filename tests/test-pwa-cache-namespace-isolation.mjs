import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync('service-worker.js', 'utf8');
const version = source.match(/const CACHE_VERSION = `\$\{CACHE_NAMESPACE\}-(v\d+)`;/)?.[1];
assert.ok(version);
const current = [
  `david-porto-pwa-${version}-static`,
  `david-porto-pwa-${version}-pages`
];
const obsolete = [
  'david-porto-pwa-v1-static',
  'david-porto-pwa-v1-pages',
  'david-porto-pwa-v15-static'
];
const unrelated = [
  'another-application-cache',
  'david-porto-independent-cache',
  'other-pwa-v1-static'
];
const keys = [...current, ...obsolete, ...unrelated];
const deleted = [];
const listeners = new Map();
const sandbox = {
  URL, Request, Response, Headers, console,
  caches: {
    keys: async () => keys,
    delete: async key => { deleted.push(key); return true; }
  },
  self: {
    location: { origin: 'https://davidportodiaz.com' },
    addEventListener: (name, handler) => listeners.set(name, handler),
    clients: { claim: async () => {} }
  }
};
vm.runInNewContext(source, sandbox);
let activation;
listeners.get('activate')({ waitUntil: promise => { activation = Promise.resolve(promise); } });
assert.ok(activation);
await activation;
for (const key of obsolete) assert.ok(deleted.includes(key), `Obsolete cache retained: ${key}`);
for (const key of [...current, ...unrelated]) assert.ok(!deleted.includes(key), `Protected cache deleted: ${key}`);
assert.equal(new Set(deleted).size, deleted.length);
console.log('PASS: cache cleanup respects namespace isolation');