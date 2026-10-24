import assert from 'node:assert/strict';
import { createWorker } from '../qa/errores-progresivo-sw-fixture.mjs';
const sw = createWorker(async () => new Response('<h1>Actual</h1>', {
  headers: { 'Content-Type': 'text/html' },
}));
sw.setPutFailure(name => name === sw.pageCache);
const result = await sw.fetch(sw.request('/herramientas/', { mode: 'navigate' }));
assert.equal(result.intercepted, true);
assert.equal(result.response.status, 200);
assert.match(await result.response.text(), /Actual/,
  'CacheStorage quota must not turn a successful online navigation into an error');
console.log('PASS online navigation survives CacheStorage quota errors');
