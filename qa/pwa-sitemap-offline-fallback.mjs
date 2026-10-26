import assert from 'node:assert/strict';
import vm from 'node:vm';
import { readFileSync } from 'node:fs';

const origin = 'https://local.test';
const url = origin + '/sitemap.xml';
const handlers = {};
const stored = new Map();
let online = true;
const cache = {
  match: async request => stored.get(typeof request === 'string' ? new URL(request, origin).href : request.url)?.clone(),
  put: async (request, response) => stored.set(request.url, response.clone())
};
const self = {
  location: { origin },
  addEventListener: (name, callback) => { handlers[name] = callback; }
};
vm.runInNewContext(readFileSync('service-worker.js', 'utf8'), {
  self, URL, Request, Response, Headers, console,
  caches: { open: async () => cache },
  fetch: async () => {
    if (!online) throw new Error('Network unavailable');
    return new Response('<urlset>PUBLICADO</urlset>', {
      headers: { 'Content-Type': 'application/xml' }
    });
  }
});

async function requestSitemap() {
  let pending;
  handlers.fetch({
    request: new Request(url),
    respondWith: value => { pending = value; },
    waitUntil: () => {}
  });
  assert.ok(pending, '/sitemap.xml: el worker no interceptó la petición');
  return pending;
}

const first = await requestSitemap();
assert.equal(first.status, 200, '/sitemap.xml: HTTP inicial incorrecto');
assert.equal(await first.text(), '<urlset>PUBLICADO</urlset>');
assert.ok(stored.has(url), '/sitemap.xml: no se almacenó la respuesta válida');

online = false;
const offline = await requestSitemap();
assert.equal(offline.status, 200, '/sitemap.xml: HTTP sin conexión incorrecto');
assert.equal(await offline.text(), '<urlset>PUBLICADO</urlset>', '/sitemap.xml: se perdió la copia publicada');
console.log('PASS sitemap offline fallback');