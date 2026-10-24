import assert from 'node:assert/strict';
import { browserCase, DIRECTORY } from './recursos-risk-harness.mjs';

await browserCase(DIRECTORY, async page => {
  const requests = [];
  const errors = [];
  page.on('request', request => requests.push(request.url()));
  page.on('pageerror', error => errors.push(error.message));

  const result = await page.evaluate(() => {
    const input = document.querySelector('[data-wt-search]');
    const count = document.querySelector('[data-wt-count]');
    const start = performance.now();
    for (let i = 0; i < 300; i++) {
      input.value = i % 3 === 0 ? 'scrivener' : i % 3 === 1 ? 'epub' : 'ninguna-qa-783';
      input.dispatchEvent(new Event('input', { bubbles: true }));
    }
    return { elapsed: performance.now() - start, final: count.textContent.trim() };
  });
  assert.ok(result.elapsed < 8000, `Filtros lentos: ${result.elapsed.toFixed(1)} ms`);
  assert.equal(result.final, '0 herramientas');
  assert.deepEqual(requests, [], 'El filtrado no debe consultar recursos remotos ni locales');
  assert.deepEqual(errors, []);
  console.log(`PASS recursos: 300 actualizaciones en ${result.elapsed.toFixed(1)} ms`);
});
