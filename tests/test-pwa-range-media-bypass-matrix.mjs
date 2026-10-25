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

const cases = [
  { path: '/assets/video.mp4', destination: 'video', range: null },
  { path: '/assets/audio.mp3', destination: 'audio', range: null },
  { path: '/assets/video.mp4', destination: '', range: 'bytes=0-1023' },
  { path: '/assets/document.pdf', destination: '', range: 'bytes=100-' },
  { path: '/assets/image.webp', destination: 'image', range: 'bytes=-500' },
  { path: '/assets/data.bin', destination: '', range: 'bytes=0-99,200-299' }
];
for (const item of cases) {
  let intercepted = false;
  const headers = new Headers();
  if (item.range) headers.set('Range', item.range);
  handler({
    request: {
      method: 'GET',
      url: `https://davidportodiaz.com${item.path}`,
      mode: 'cors',
      destination: item.destination,
      headers
    },
    respondWith: () => { intercepted = true; },
    waitUntil: () => {}
  });
  assert.equal(intercepted, false, `Media/range intercepted: ${JSON.stringify(item)}`);
}
console.log('PASS: media and range requests bypass the worker');