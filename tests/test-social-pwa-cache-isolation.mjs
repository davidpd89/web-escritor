import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync(new URL('../service-worker.js', import.meta.url), 'utf8');
const origin = 'https://davidportodiaz.com';
const social = origin + '/redes-sociales/';
const other = origin + '/libros/';

function setup() {
  const pages = new Map([[social, new Response('<h1>Redes sociales</h1>', {headers: {'Content-Type': 'text/html'}})]]);
  const staticFiles = new Map([[origin + '/offline.html', new Response('<h1>Sin conexión</h1>', {headers: {'Content-Type': 'text/html'}})]]);
  const makeCache = entries => ({
    match: async request => entries.get(typeof request === 'string' ? new URL(request, origin).href : request.url)?.clone(),
    put: async (request, response) => entries.set(request.url, response.clone())
  });
  const context = vm.createContext({
    URL, Request, Response, Set, console,
    self: {location: {origin}, addEventListener() {}},
    caches: {open: async name => makeCache(name.endsWith('-pages') ? pages : staticFiles)},
    fetch: async () => {throw new Error('offline');}
  });
  vm.runInContext(source, context);
  return context;
}

test('/redes-sociales/: la caché no contamina otra navegación offline', async () => {
  const context = setup();
  const navigate = vm.runInContext('networkFirstPage', context);
  const socialResponse = await navigate(new Request(social));
  assert.match(await socialResponse.text(), /Redes sociales/);
  const otherResponse = await navigate(new Request(other));
  const body = await otherResponse.text();
  assert.match(body, /Sin conexión/, '/libros/: falta el fallback offline');
  assert.doesNotMatch(body, /Redes sociales/, '/libros/: se ha servido una página de otra ruta');
});