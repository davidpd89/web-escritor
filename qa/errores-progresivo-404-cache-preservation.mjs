import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createWorker } from './errores-progresivo-sw-fixture.mjs';

const path = '/libros/';
const html = readFileSync(new URL('../libros/index.html', import.meta.url), 'utf8');
assert.match(html, /<main\b/i, `${path}: falta contenido editorial real`);

const worker = createWorker(async () => new Response(html, {
  status: 200,
  headers: { 'Content-Type': 'text/html; charset=utf-8' }
}));
const request = worker.request(path, { mode: 'navigate' });

const first = await worker.fetch(request);
assert.equal(first.response.status, 200, `${path}: la primera navegación debe devolver 200`);
assert.equal(await first.response.text(), html, `${path}: el contenido inicial no coincide con el HTML publicado`);

worker.setNetwork(async () => new Response('Página no encontrada', {
  status: 404,
  headers: { 'Content-Type': 'text/html' }
}));
const missing = await worker.fetch(request);
assert.equal(missing.response.status, 404, `${path}: el error HTTP debe conservar su estado`);

worker.setNetwork(async () => { throw new TypeError('Failed to fetch'); });
const recovered = await worker.fetch(request);
assert.equal(recovered.response.status, 200, `${path}: el 404 ha sustituido la copia válida`);
assert.equal(await recovered.response.text(), html, `${path}: no se recuperó el documento editorial anterior`);
console.log('PASS: 404 no sobrescribe la última página editorial válida');