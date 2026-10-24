import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { localPage, ORIGIN } from './home-family-local-fixture.mjs';

const browser = await chromium.launch({ headless: true });
try {
  for (const viewport of [
    { width: 390, height: 844 },
    { width: 1280, height: 900 }
  ]) {
    const { context, page } = await localPage(browser, { viewport });
    await page.addInitScript(() => sessionStorage.setItem('dp-intro-seen', '1'));
    await page.route('**/assets/assistant-widget.js*', route => route.abort());
    await page.goto(ORIGIN + '/');

    const trigger = page.locator('[data-assistant-search-open]').first();
    await trigger.click();
    await page.waitForURL('**/asistente/', { timeout: 12000 });

    assert.equal(new URL(page.url()).pathname, '/asistente/');
    assert.equal(await page.locator('main').count(), 1);
    assert.equal(await page.locator('body').isVisible(), true);
    await context.close();
  }
  console.log('PASS home-assistant-failure-journey');
} finally {
  await browser.close();
}