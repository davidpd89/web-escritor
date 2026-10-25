import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const listeners = new Map();
const sandbox = {
  URL, Request, Response, Headers, console,
  self: {
    location: { origin: 'https://davidportodiaz.com' },
    addEventListener: (name, callback) => listeners.set(name, callback)
  }
};
vm.runInNewContext(fs.readFileSync('service-worker.js', 'utf8'), sandbox);
const handler = listeners.get('fetch');
assert.equal(typeof handler, 'function');

function intercepted(method, url) {
  let count = 0;
  handler({
    request: { method, url, mode: 'cors', destination: '', headers: new Headers() },
    respondWith: () => { count++; },
    waitUntil: () => {}
  });
  return count;
}

const local = 'https://davidportodiaz.com/assets/data.json';
for (const method of ['POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']) {
  assert.equal(intercepted(method, local), 0, `${method} intercepted`);
}
for (const origin of [
  'https://example.com',
  'https://cdn.example.com',
  'https://davidportodiaz.com.evil.example',
  'http://davidportodiaz.com',
  'https://sub.davidportodiaz.com'
]) {
  assert.equal(intercepted('GET', `${origin}/assets/data.json`), 0, `External origin intercepted: ${origin}`);
}
console.log('PASS: unsafe methods and external origins bypass the worker');