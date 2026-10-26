import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const root = new URL('../', import.meta.url);
const html = fs.readFileSync(new URL('redes-sociales/index.html', root), 'utf8');
const source = fs.readFileSync(new URL('service-worker.js', root), 'utf8');
const origin = 'https://davidportodiaz.com';
const styles = [...html.matchAll(/<link\b[^>]*rel="stylesheet"[^>]*href="([^"]+\.css\?v=[^"]+)"/g)].map(match => match[1]);

function setup() {
  const entries = new Map();
  let online = true;
  const context = vm.createContext({
    URL, Request, Response, Set, console,
    self: {location: {origin}, addEventListener() {}},
    caches: {open: async () => ({
      put: async (request, response) => entries.set(request.url, response.clone()),
      match: async request => entries.get(request.url)?.clone()
    })},
    fetch: async request => {
      if (!online) throw new Error('offline');
      return new Response('/* ' + request.url + ' */', {status: 200, headers: {'Content-Type': 'text/css'}});
    }
  });
  vm.runInContext(source, context);
  return {context, entries, offline: () => {online = false;}};
}

test('/redes-sociales/: todos los CSS versionados conservan su identidad offline', async () => {
  assert.ok(styles.length > 0, '/redes-sociales/: no se descubrieron CSS versionados');
  const h = setup();
  const load = vm.runInContext('networkFirstStatic', h.context);
  for (const href of styles) {
    const request = new Request(new URL(href, origin));
    const response = await load(request);
    assert.equal(response.status, 200, `${href}: carga inicial fallida`);
    assert.ok(h.entries.has(request.url), `${href}: clave versionada ausente`);
  }
  h.offline();
  for (const href of styles) {
    const request = new Request(new URL(href, origin));
    const response = await load(request);
    assert.equal(response.status, 200, `${href}: CSS no recuperado offline`);
    assert.match(await response.text(), /\/\* https:\/\//, `${href}: contenido CSS recuperado incorrecto`);
  }
});