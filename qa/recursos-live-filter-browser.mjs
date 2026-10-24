import assert from 'node:assert/strict';
import { browserCase, DIRECTORY } from './recursos-risk-harness.mjs';

await browserCase(DIRECTORY, async page => {
  const count = page.locator('[data-wt-count]');
  const empty = page.locator('[data-wt-empty]');
  assert.equal(await count.getAttribute('aria-live'), 'polite');
  assert.equal((await count.innerText()).trim(), '8 herramientas');
  assert.equal(await empty.isHidden(), true);

  await page.locator('#wt-search').fill('qa-inexistente-5729');
  assert.equal((await count.innerText()).trim(), '0 herramientas');
  assert.equal(await empty.isVisible(), true);
  assert.match(await empty.innerText(), /no hay herramientas/i);

  await page.locator('#wt-search').fill('scrivener');
  assert.equal((await count.innerText()).trim(), '1 herramienta');
  assert.equal(await empty.isHidden(), true);

  await page.locator('[data-wt-clear]').click();
  assert.equal((await count.innerText()).trim(), '8 herramientas');
  assert.equal(await empty.isHidden(), true);
  console.log('PASS recursos: estado accesible de filtros');
});
