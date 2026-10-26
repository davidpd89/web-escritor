import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync(new URL('../service-worker.js', import.meta.url), 'utf8');
const html = fs.readFileSync(new URL('../redes-sociales/index.html', import.meta.url), 'utf8');
const origin = 'https://davidportodiaz.com';

function harness() {
  const entries = new Map();
  let online = true;
  const cache = {
    put: async (request, response) => entries.set(request.url, response.clone()),
    match: async request => entries.get(typeof request === 'string' ? new URL(request, origin).href : request.url)?.clone()
  };
  const context = vm.createContext({
    URL, Request, Response, Set, console,
    self: {location: {origin}, addEventListener() {}},
    caches: {open: async () => cache},
    fetch: async request => {
      if (!online) throw new Error('network offline');
      return new Response(html, {status: 200, headers: {'Content-Type': 'text/html'}});
    }
  });
  vm.runInContext(source, context, {filename: 'service-worker.js'});
  return {context, entries, setOnline: value => {online = value;}};
}

test('/redes-sociales/: una navegación visitada sobrevive a la pérdida de conexión', async () => {
  const h = harness();
  const request = new Request(origin + '/redes-sociales/');
  const first = await vm.runInContext('networkFirstPage', h.context)(request);
  assert.equal(first.status, 200);
  assert.equal(h.entries.size, 1, '/redes-sociales/: la visita no se guardó');
  h.setOnline(false);
  const recovered = await vm.runInContext('networkFirstPage', h.context)(request);
  assert.equal(recovered.status, 200, '/redes-sociales/: no se recuperó la página visitada');
  assert.match(await recovered.text(), /Redes sociales: seguidores verificados/, '/redes-sociales/: contenido recuperado incorrecto');
});