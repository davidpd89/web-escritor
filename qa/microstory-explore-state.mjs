import assert from 'node:assert/strict';
import {withPage} from './microstory-offline-harness.mjs';

for (const width of [390,1280]) {
  await withPage(async ({page}) => {
    const opener = page.locator('[data-explore-open]').first();
    const dialog = page.locator('[data-explore-dialog]');
    const toggle = dialog.locator('.explore-row__toggle').first();
    for (let cycle=0;cycle<3;cycle++) {
      await opener.click();
      assert.equal(await opener.getAttribute('aria-expanded'),'true');
      assert.equal(await dialog.evaluate(d => d.open),true);
      assert.equal(await page.locator('[data-explore-close]').evaluate(e => document.activeElement===e),true);
      for (const expected of ['true','false','true']) {
        await toggle.click();
        assert.equal(await toggle.getAttribute('aria-expanded'),expected);
        const hidden = await toggle.evaluate(b => document.getElementById(b.getAttribute('aria-controls')).hidden);
        assert.equal(hidden,expected==='false');
      }
      await page.keyboard.press('Escape');
      await dialog.waitFor({state:'hidden'});
      await page.waitForTimeout(120);
      assert.equal(await opener.getAttribute('aria-expanded'),'false');
      assert.equal(await opener.evaluate(e => document.activeElement===e),true);
      assert.equal(await page.evaluate(() => document.documentElement.classList.contains('explore-open')),false);
      assert.equal(await page.evaluate(() => document.querySelector('main').inert),false);
    }
  },width);
}
console.log('PASS microstory explore state');
