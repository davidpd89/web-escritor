import assert from 'node:assert/strict';
import { createWorker } from './errores-progresivo-sw-fixture.mjs';

const path = '/assets/david-porto-favicon.png';
let partial = false;
const worker = createWorker(async () => partial
  ? new Response('part', {
      status: 206,
      headers: { 'Content-Type': 'image/png', 'Content-Range': 'bytes 0-3/12' }
    })
  : new Response('complete-img', {
      status: 200,
      headers: { 'Content-Type': 'image/png' }
    }));
const request = worker.request(path, { destination: 'image' });

const first = await worker.fetch(request);
assert.equal(first.response.status, 200, `${path}: respuesta inicial`);
assert.equal(await first.response.text(), 'complete-img');

partial = true;
const second = await worker.fetch(request);
assert.equal(second.response.status, 200, `${path}: una respuesta parcial no debe desplazar la imagen completa`);
assert.equal(await second.response.text(), 'complete-img', `${path}: contenido visible tras HTTP 206`);

const cached = await (await worker.caches.open(worker.staticCache)).match(request);
assert(cached, `${path}: falta la imagen completa en caché`);
assert.equal(cached.status, 200, `${path}: STATIC_CACHE contiene HTTP 206`);
assert.equal(await cached.text(), 'complete-img', `${path}: imagen truncada almacenada`);
console.log('PASS partial image cache integrity');
