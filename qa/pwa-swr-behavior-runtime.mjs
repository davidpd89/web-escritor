import assert from 'node:assert/strict';
import vm from 'node:vm';
import { readFileSync } from 'node:fs';

const handlers = {};
const url = 'https://local.test/assets/portada.webp';
const entries = new Map([[url, new Response('OLD IMAGE')]]);
const cache = {
  match: async req => entries.get(req.url)?.clone(),
  put: async (req, res) => entries.set(req.url, res.clone())
};
let online = true;
let fetchCount = 0;
const self = {
  location: { origin: 'https://local.test' },
  addEventListener: (type, fn) => { handlers[type] = fn; }
};
vm.runInNewContext(readFileSync('service-worker.js', 'utf8'), {
  self, caches: { open: async () => cache }, URL, Headers, Request, Response,
  fetch: async () => {
    fetchCount++;
    if (!online) throw Error('No network');
    return new Response('NEW IMAGE');
  }
});
async function requestImage() {
  let response;
  const background = [];
  handlers.fetch({
    request: { url, method: 'GET', destination: 'image', mode: 'cors', headers: new Headers() },
    respondWith: promise => { response = promise; },
    waitUntil: promise => { background.push(promise); }
  });
  const result = await response;
  const bytes = await result.text();
  await Promise.all(background);
  return bytes;
}
assert.equal(await requestImage(), 'OLD IMAGE', 'Cached first paint lost');
assert.equal(await entries.get(url).clone().text(), 'NEW IMAGE', 'Background refresh missing');
assert.equal(fetchCount, 1);
online = false;
assert.equal(await requestImage(), 'NEW IMAGE', 'Offline update not available');
console.log('PASS: stale first paint, revalidated cache and offline reuse');
