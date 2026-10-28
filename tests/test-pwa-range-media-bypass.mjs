import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const listeners = new Map();
const sandbox = {
  URL, Request, Response, Headers, console,
  caches: { open: async () => { throw new Error('CacheStorage should not be used'); } },
  self: {
    location: { origin: 'https://davidportodiaz.com' },
    addEventListener: (type, callback) => listeners.set(type, callback),
    skipWaiting: async () => {},
    clients: { claim: async () => {} }
  }
};
vm.runInNewContext(fs.readFileSync('service-worker.js', 'utf8'), sandbox);
function dispatch(path, destination, range) {
  let intercepted = false;
  const headers = new Headers();
  if (range) headers.set('Range', range);
  listeners.get('fetch')({
    request: { method: 'GET', url: `https://davidportodiaz.com${path}`, mode: 'cors', destination, headers },
    respondWith: (responsePromise) => {
    intercepted = true;
    Promise.resolve(responsePromise).catch(() => {});
  },
    waitUntil: () => {}
  });
  return intercepted;
}
for (const [path, destination, range] of [
  ['/assets/video.mp4', 'video', null],
  ['/assets/audio.mp3', 'audio', null],
  ['/assets/file.bin', '', 'bytes=0-1023'],
  ['/assets/app.js', 'script', 'bytes=10-20'],
  ['/assets/movie.mp4', '', 'bytes=-500']
]) {
  assert.equal(dispatch(path, destination, range), false, path);
}
assert.equal(dispatch('/assets/app.js', 'script', null), true);
console.log('PASS: media and range bypass');