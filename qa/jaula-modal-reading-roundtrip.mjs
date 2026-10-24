import assert from 'node:assert/strict';
import { withJaula } from './jaula-local-fixture.mjs';

for (const width of [390, 768, 1440]) {
  await withJaula(async ({ page }) => {
    await page.locator('.excerpt-field p').nth(50).scrollIntoViewIfNeeded();
    const opener = page.locator('[data-explore-open]');
    await opener.focus();
    const before = await page.evaluate(() => scrollY);
    await page.keyboard.press('Enter');
    await page.waitForFunction(() => document.querySelector('#explore-dialog')?.open === true);
    assert.equal(await opener.getAttribute('aria-expanded'), 'true');
    assert.equal(await page.locator('#explore-dialog').evaluate(el => el.contains(document.activeElement)), true, `${width}: foco fuera del modal`);
    await page.keyboard.press('Escape');
    await page.waitForFunction(() => document.querySelector('#explore-dialog')?.open === false);
    assert.equal(await opener.getAttribute('aria-expanded'), 'false');
    assert.equal(await opener.evaluate(el => document.activeElement === el), true, `${width}: foco no restaurado`);
    await page.waitForFunction(previous => Math.abs(scrollY - previous) <= 10, before, { timeout: 3000 });
  }, { width });
}
console.log('jaula-modal-reading-roundtrip: OK');
