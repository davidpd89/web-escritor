import assert from 'node:assert/strict';
import { browserCase, DIRECTORY } from './recursos-risk-harness.mjs';

await browserCase(DIRECTORY, async page => {
  assert.equal(await page.locator('.wt-card:visible').count(), 8);
  const form = page.locator('[data-wt-filters]');
  assert.equal(await form.count(), 1);
  const controls = form.locator('input, select, button');
  const allDisabled = await controls.evaluateAll(nodes => nodes.every(node => node.disabled));
  const warning = await page.locator('main').innerText();
  const hasFallbackNotice = /filtros?.{0,100}(requiere|necesita|sin javascript|no disponible)/i.test(warning);
  assert.ok(allDisabled || hasFallbackNotice,
    'Sin JavaScript, los filtros parecen funcionales pero no modifican resultados');
  assert.equal(await page.locator('.wt-card').count(), 8);
  console.log('PASS recursos: degradación honesta sin JavaScript');
}, { javaScriptEnabled: false });
