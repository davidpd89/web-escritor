import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const listeners = new Map();
const sandbox = {
  URL, Request, Response, Headers, console,
  caches: {
    open: async () => ({ match: async () => null, put: async () => {}, addAll: async () => {} }),
    keys: async () => [], delete: async () => true
  },
  fetch: async () => new Response('OK', { status: 200 }),
  self: {
    location: { origin: 'https://davidportodiaz.com' },
    addEventListener: (type, fn) => listeners.set(type, fn),
    skipWaiting: async () => {}, clients: { claim: async () => {} }
  }
};
vm.runInNewContext(fs.readFileSync('service-worker.js', 'utf8'), sandbox);
const origin = 'https://davidportodiaz.com';
const cases = [
  { label: 'POST formulario', method: 'POST', url: origin + '/newsletter/' },
  { label: 'HEAD', method: 'HEAD', url: origin + '/manifest.json' },
  { label: 'PUT API', method: 'PUT', url: origin + '/api/assistant' },
  { label: 'otro origen', method: 'GET', url: 'https://example.invalid/assets/logo.webp' },
  { label: 'Range imagen', method: 'GET', url: origin + '/assets/cover.webp', range: 'bytes=0-99' },
  { label: 'Range módulo', method: 'GET', url: origin + '/assets/module.mjs', range: 'bytes=0-99' },
  { label: 'vídeo', method: 'GET', url: origin + '/assets/video.mp4', destination: 'video' },
  { label: 'audio', method: 'GET', url: origin + '/assets/audio.mp3', destination: 'audio' }
];
function dispatch(item) {
  let responded = false;
  let waited = false;
  listeners.get('fetch')({
    request: {
      method: item.method, url: item.url, mode: 'cors',
      destination: item.destination || '',
      headers: new Headers(item.range ? { Range: item.range } : {})
    },
    respondWith: () => { responded = true; },
    waitUntil: () => { waited = true; }
  });
  return { responded, waited };
}
for (const item of cases) {
  assert.deepEqual(dispatch(item), { responded: false, waited: false }, item.label);
}
assert.equal(dispatch({ method: 'GET', url: origin + '/assets/cover.webp', destination: 'image' }).responded, true);
console.log('PASS: matriz de peticiones excluidas de la PWA');