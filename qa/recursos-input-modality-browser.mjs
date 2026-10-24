import assert from 'node:assert/strict';
import { browserCase, DIRECTORY } from './recursos-risk-harness.mjs';

const visible = page => page.locator('.wt-card:visible').evaluateAll(nodes =>
  nodes.map(node => node.dataset.name).sort());

await browserCase(DIRECTORY, async page => {
  await page.locator('#wt-stage').selectOption('planificacion');
  await page.locator('[data-wt-no-account]').check();
  const mouse = await visible(page);
  assert.ok(mouse.length > 0);

  await page.locator('[data-wt-clear]').click();
  await page.locator('#wt-stage').focus();
  await page.keyboard.press('Home');
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Tab');
  assert.equal(await page.locator('#wt-stage').inputValue(), 'planificacion');

  await page.locator('[data-wt-no-account]').focus();
  await page.keyboard.press('Space');
  assert.equal(await page.locator('[data-wt-no-account]').isChecked(), true);
  assert.deepEqual(await visible(page), mouse);
  console.log('PASS recursos: teclado y ratón equivalentes');
});
