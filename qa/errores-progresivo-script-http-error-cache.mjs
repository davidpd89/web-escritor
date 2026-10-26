import assert from 'node:assert/strict';
import { createWorker } from './errores-progresivo-sw-fixture.mjs';

const path = '/script.js';
let failing = false;
const worker = createWorker(async () => failing
  ? new Response('Service unavailable', {
      status: 503,
      headers: { 'Content-Type': 'text/plain' }
    })
  : new Response('window.__qaScriptReady = true;', {
      status: 200,
      headers: { 'Content-Type': 'text/javascript' }
    }));
const request = worker.request(path, { destination: 'script' });

const initial = await worker.fetch(request);
assert.equal(initial.response.status, 200, `${path}: descarga inicial`);
assert.equal(await initial.response.text(), 'window.__qaScriptReady = true;');

failing = true;
const failed = await worker.fetch(request);
assert.equal(failed.response.status, 503, `${path}: un error HTTP del servidor debe conservar su estado`);

const cached = await (await worker.caches.open(worker.staticCache)).match(request);
assert(cached, `${path}: desapareció la versión JavaScript válida`);
assert.equal(cached.status, 200, `${path}: una respuesta de error reemplazó el script`);
assert.equal(await cached.text(), 'window.__qaScriptReady = true;', `${path}: el contenido del error contaminó STATIC_CACHE`);

worker.setNetwork(async () => { throw new Error('network disconnected'); });
const offline = await worker.fetch(request);
assert.equal(offline.response.status, 200, `${path}: no se recuperó el script válido tras perder la conexión`);
assert.equal(await offline.response.text(), 'window.__qaScriptReady = true;', `${path}: fallback JavaScript incorrecto`);
console.log('PASS script HTTP error cache integrity');
