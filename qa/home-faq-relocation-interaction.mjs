import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { localPage, readyHome } from './home-family-local-fixture.mjs';

const browser = await chromium.launch({ headless: true });
try {
  for (const width of [320, 390, 1280]) {
    const { context, page } = await localPage(browser, {
      viewport: { width, height: 900 }
    });
    await readyHome(page);

    const master = page.locator('#faq');
    assert.equal(await master.count(), 1);
    assert.equal(await master.evaluate(el => !!el.closest('.editorial-home-flow')), true);
    assert.equal(await master.isVisible(), true);

    const questions = master.locator('.faq-native > details');
    assert.equal(await questions.count(), 8);
    assert.equal(await master.getAttribute('open'), null);

    await master.locator(':scope > summary').click();
    assert.equal(await master.evaluate(el => el.open), true);
    await questions.first().locator('summary').click();
    assert.equal(await questions.first().evaluate(el => el.open), true);
    assert.equal(await questions.first().locator('a[href]').count() > 0, true);

    const second = questions.nth(1).locator('summary');
    await second.focus();
    await page.keyboard.press('Enter');
    assert.equal(await questions.nth(1).evaluate(el => el.open), true);

    await master.locator(':scope > summary').click();
    assert.equal(await master.evaluate(el => el.open), false);
    await context.close();
  }
  console.log('PASS home-faq-relocation-interaction');
} finally {
  await browser.close();
}