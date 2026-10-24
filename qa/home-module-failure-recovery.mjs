import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { localPage, ORIGIN } from './home-family-local-fixture.mjs';

const browser = await chromium.launch({ headless: true });
try {
  for (const blocked of [
    'v1-home-editorial-v3.js',
    'editorial-public-facts.mjs'
  ]) {
    const { context, page } = await localPage(browser);
    await page.addInitScript(() => sessionStorage.setItem('dp-intro-seen', '1'));
    await page.route(`**/assets/${blocked}*`, route => route.abort());
    await page.goto(ORIGIN + '/', { waitUntil: 'load' });

    await page.waitForFunction(() => {
      const river = document.querySelector('.river-grid');
      return river && getComputedStyle(river).visibility === 'visible';
    }, null, { timeout: 8500 });

    assert.notEqual(await page.locator('.river-grid').count(), 0);
    assert.equal(await page.locator('[data-editorial-home-flow]').count(), 0);
    assert.equal(await page.locator('.river-grid a[href="/las-manecillas-del-recuerdo/"]').first().isVisible(), true);
    assert.equal(await page.locator('#newsletter').isVisible(), true);

    await page.locator('.river-grid a[href="/las-manecillas-del-recuerdo/"]').first().click();
    await page.waitForURL('**/las-manecillas-del-recuerdo/');
    assert.equal(new URL(page.url()).pathname, '/las-manecillas-del-recuerdo/');
    await context.close();
  }
  console.log('PASS home-module-failure-recovery');
} finally {
  await browser.close();
}