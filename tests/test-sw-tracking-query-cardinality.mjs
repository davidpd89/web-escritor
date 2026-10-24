import assert from 'node:assert/strict';
import { createWorker } from '../qa/errores-progresivo-sw-fixture.mjs';
const sw = createWorker(async () => new Response('<h1>Ficha</h1>', {
  headers: { 'Content-Type': 'text/html' },
}));
for (const path of [
  '/libros/?utm_source=instagram',
  '/libros/?utm_source=threads',
  '/libros/?fbclid=campaign-one',
  '/libros/?gclid=campaign-two',
]) {
  const result = await sw.fetch(sw.request(path, { mode: 'navigate' }));
  assert.equal(result.response.status, 200);
}
const entries = sw.entries(sw.pageCache).filter(url => new URL(url).pathname === '/libros/');
assert.equal(entries.length, 1,
  `Four equivalent marketing URLs generated ${entries.length} cache records`);
console.log('PASS tracking-query cache deduplication');
