import assert from 'node:assert/strict';
import { createWorker } from './errores-progresivo-sw-fixture.mjs';

const path = '/assets/david-porto-favicon.png';
let status = 200;
const worker = createWorker(async () => new Response(status === 200 ? 'valid-image' : 'server-error', {
  status,
  headers: { 'Content-Type': status === 200 ? 'image/png' : 'text/plain' }
}));
const request = worker.request(path, { destination: 'image' });

const first = await worker.fetch(request);
assert.equal(first.response.status, 200, `${path}: descarga inicial`);
assert.equal(await first.response.text(), 'valid-image', `${path}: bytes iniciales`);

status = 500;
const second = await worker.fetch(request);
assert.equal(second.response.status, 200, `${path}: la revalidación HTTP 500 no debe sustituir la imagen válida`);
assert.equal(await second.response.text(), 'valid-image', `${path}: contenido visible tras el error`);

const cached = await (await worker.caches.open(worker.staticCache)).match(request);
assert(cached, `${path}: desapareció la imagen de STATIC_CACHE`);
assert.equal(await cached.text(), 'valid-image', `${path}: la respuesta HTTP 500 contaminó la caché`);
console.log('PASS image revalidation HTTP error');
