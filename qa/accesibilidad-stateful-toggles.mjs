import assert from 'node:assert/strict';
import { check } from './accesibilidad-fixture.mjs';

await check(async ({ page }) => {
  await page.locator('[data-explore-open]').first().click();
  const dialog = page.locator('[data-explore-dialog]');
  const toggles = dialog.locator('.explore-row__toggle');
  const count = await toggles.count();
  assert.ok(count >= 5);
  const sequence = [0, 2, 4, 2, 1, 0, 3, 4, 1, 3, 0, 0];
  for (const index of sequence) {
    const toggle = toggles.nth(index);
    const controlled = await toggle.getAttribute('aria-controls');
    assert.ok(controlled);
    const panel = dialog.locator(`[id='${controlled}']`);
    assert.equal(await panel.count(), 1);
    const before = await toggle.getAttribute('aria-expanded');
    await toggle.click();
    const after = await toggle.getAttribute('aria-expanded');
    assert.notEqual(after, before);
    assert.equal(await panel.evaluate(el => el.hidden), after === 'false');
  }
  for (let i = 0; i < 30; i++) {
    await page.keyboard.press(i % 7 === 0 ? 'Shift+Tab' : 'Tab');
    assert.equal(await page.evaluate(() => document.querySelector('[data-explore-dialog]').contains(document.activeElement)), true, `Tab ${i}`);
  }
  await page.keyboard.press('Escape');
  await page.waitForFunction(() => !document.querySelector('[data-explore-dialog]').open);
  await page.locator('[data-explore-open]').first().click();
  assert.equal(await dialog.count(), 1);
  assert.equal(await toggles.count(), count);
});
console.log('accesibilidad-stateful-toggles: PASS');
