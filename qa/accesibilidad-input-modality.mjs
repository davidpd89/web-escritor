import assert from 'node:assert/strict';
import { check } from './accesibilidad-fixture.mjs';

await check(async ({ page }) => {
  for (const mode of ['pointer', 'Enter', 'Space']) {
    await page.reload({ waitUntil: 'load' });
    const opener = page.locator('[data-explore-open]').first();
    await opener.focus();
    if (mode === 'pointer') await opener.click();
    else await page.keyboard.press(mode);
    assert.equal(await page.locator('[data-explore-dialog]').evaluate(el => el.open), true, mode);
    assert.equal(await opener.getAttribute('aria-expanded'), 'true', mode);
    const toggle = page.locator('.explore-row__toggle').first();
    await toggle.focus();
    if (mode === 'pointer') await toggle.click();
    else await page.keyboard.press(mode);
    assert.equal(await toggle.getAttribute('aria-expanded'), 'true', mode);
    const id = await toggle.getAttribute('aria-controls');
    assert.equal(await page.locator(`#${id}`).evaluate(el => el.hidden), false, mode);
    await page.keyboard.press('Escape');
    await page.waitForFunction(() => !document.querySelector('[data-explore-dialog]').open);
    await page.waitForFunction(() => document.activeElement?.matches('[data-explore-open]'));
    assert.equal(await opener.getAttribute('aria-expanded'), 'false', mode);
  }
});
console.log('accesibilidad-input-modality: PASS');
