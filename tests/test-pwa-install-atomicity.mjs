import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync('service-worker.js', 'utf8');
const shell = source.match(/const APP_SHELL = \[([\s\S]*?)\];/);
assert.ok(shell);
const expected = [...shell[1].matchAll(/['\"]([^'\"]+)['\"]/g)].length;
assert.ok(expected > 0);

async function run(fail) {
  const listeners = new Map();
  const order = [];
  const sandbox = {
    URL, Response, Headers, console,
    Request: class { constructor(url, options) { this.url = url; this.cache = options.cache; } },
    caches: {
      open: async () => ({
        addAll: async requests => {
          order.push('addAll');
          assert.equal(requests.length, expected);
          assert.ok(requests.every(req => req.cache === 'reload'));
          if (fail) throw new Error('APP_SHELL preload failed');
          order.push('cached');
        }
      })
    },
    self: {
      location: { origin: 'https://davidportodiaz.com' },
      addEventListener: (type, fn) => listeners.set(type, fn),
      skipWaiting: async () => { order.push('skipWaiting'); },
      clients: { claim: async () => {} }
    }
  };
  vm.runInNewContext(source, sandbox);
  let installation;
  listeners.get('install')({ waitUntil: promise => { installation = promise; } });
  assert.ok(installation);
  if (fail) {
    await assert.rejects(installation, /preload failed/);
    assert.deepEqual(order, ['addAll']);
  } else {
    await installation;
    assert.deepEqual(order, ['addAll', 'cached', 'skipWaiting']);
  }
}
await run(true);
await run(false);
console.log('PASS: instalación atómica y skipWaiting posterior a la precarga');