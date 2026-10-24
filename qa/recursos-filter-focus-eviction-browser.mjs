import assert from 'node:assert/strict';
import { browserCase, DIRECTORY } from './recursos-risk-harness.mjs';

await browserCase(DIRECTORY, async page => {
  const card = page.locator('.wt-card[data-name="scrivener"]');
  await card.locator('details summary').click();
  await card.locator('.tool-source-list a').first().focus();
  assert.equal(await card.evaluate(el => el.contains(document.activeElement)), true);

  await page.evaluate(() => {
    const search = document.querySelector('[data-wt-search]');
    search.value = 'bibliogon';
    search.dispatchEvent(new Event('input', { bubbles: true }));
  });
  assert.equal(await card.isHidden(), true);
  assert.equal(await card.evaluate(el => el.contains(document.activeElement)), false,
    'El foco continúa dentro de una tarjeta oculta');
  await page.keyboard.press('Tab');
  const focus = await page.evaluate(() => {
    const el = document.activeElement;
    return Boolean(el && el !== document.body &&
      el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden');
  });
  assert.equal(focus, true, 'La tabulación debe continuar por un control visible');
  console.log('PASS recursos: recuperación del foco');
});
