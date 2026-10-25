import assert from 'node:assert/strict';
import { createWorker } from '../qa/errores-progresivo-sw-fixture.mjs';
for (const directive of ['no-store', 'private, max-age=0']) {
  const sw = createWorker(async () => new Response('personal response', {
    status: 200,
    headers: { 'Cache-Control': directive, 'Content-Type': 'text/html' },
  }));
  const req = sw.request('/zona-privada/?session=qa', { mode: 'navigate' });
  const result = await sw.fetch(req);
  assert.equal(result.response.status, 200);
  assert.equal((await result.response.text()), 'personal response');
  assert.equal((await sw.cacheFor(sw.pageCache).match(req)), undefined,
    `Cache-Control ${directive} must prohibit offline persistence`);
}
console.log('PASS no-store/private navigation isolation');
