import assert from 'node:assert/strict';
import vm from 'node:vm';
import { readFileSync } from 'node:fs';

const handlers = {};
const url = 'https://local.test/sitemap.xml';
const cacheContents = new Map([[url, new Response('<urlset>OLD</urlset>')]]);
const cache = {
  match: async req => cacheContents.get(req.url),
  put: async (req, res) => cacheContents.set(req.url, res.clone())
};
const self = {
  location: { origin: 'https://local.test' },
  addEventListener: (event, handler) => { handlers[event] = handler; }
};
vm.runInNewContext(readFileSync('service-worker.js', 'utf8'), {
  self, URL, Request, Response, Headers,
  caches: { open: async () => cache },
  fetch: async () => new Response('<urlset>NEW</urlset>', {
    headers: { 'Content-Type': 'application/xml' }
  })
});
let responsePromise;
const background = [];
handlers.fetch({
  request: { url, method: 'GET', mode: 'cors', destination: '', headers: new Headers() },
  respondWith: promise => { responsePromise = promise; },
  waitUntil: promise => background.push(promise)
});
assert.ok(responsePromise, 'Sitemap request was not handled');
const response = await responsePromise;
const body = await response.text();
await Promise.all(background);
assert.equal(body, '<urlset>NEW</urlset>', 'An online visitor received the stale sitemap');
console.log('PASS: online sitemap always reflects the current server representation');
