import assert from 'node:assert/strict';
import { browserCase, DIRECTORY } from './recursos-risk-harness.mjs';

await browserCase(DIRECTORY, async page => {
  for (let round = 0; round < 12; round++) {
    await page.locator('#wt-search').fill('no-existe-qa-123');
    await page.locator('#wt-stage').selectOption('maquetacion');
    await page.locator('#wt-price').selectOption('gratis-open-source');
    await page.locator('[data-wt-no-account]').check();
    await page.locator('[data-wt-local]').check();
    await page.locator('[data-wt-spanish]').check();
    assert.equal(await page.locator('.wt-card:visible').count(), 0);
    assert.equal(await page.locator('[data-wt-empty]').isVisible(), true);

    await page.locator('[data-wt-clear]').click();
    assert.equal(await page.locator('#wt-search').inputValue(), '');
    assert.equal(await page.locator('#wt-stage').inputValue(), '');
    assert.equal(await page.locator('#wt-price').inputValue(), '');
    for (const attr of ['no-account', 'local', 'spanish']) {
      assert.equal(await page.locator(`[data-wt-${attr}]`).isChecked(), false);
    }
    assert.equal(await page.locator('.wt-card:visible').count(), 8);
    assert.equal(await page.locator('[data-wt-empty]').isHidden(), true);
    assert.equal(await page.evaluate(() => document.activeElement?.id), 'wt-search');
  }
  console.log('PASS recursos: transiciones y limpieza repetida');
});
