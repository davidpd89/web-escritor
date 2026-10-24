import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  for (const modality of ['mouse', 'keyboard', 'touch']) {
    const context = await browser.newContext({ viewport: { width: 390, height: 900 }, hasTouch: modality === 'touch', reducedMotion: 'reduce' });
    await context.route('**/*', route => route.request().url().startsWith(origin) ? route.continue() : route.abort());
    const page = await context.newPage();
    await page.goto(`${origin}/las-manecillas-del-recuerdo/fragmentos/`);
    for (const id of ['fragmento-1', 'fragmento-2', 'fragmento-3']) {
      const link = page.locator(`[data-fragment-link="${id}"]`);
      if (modality === 'keyboard') {
        await link.focus();
        await page.keyboard.press('Enter');
      } else if (modality === 'touch') {
        await link.tap();
      } else {
        await link.click();
      }
      await page.waitForURL(url => url.hash === `#${id}`);
      await page.waitForFunction(expected => document.querySelector(`[data-fragment-link="${expected}"]`)?.dataset.current === 'true', id);
      assert.equal(await page.locator('[data-fragment-link][data-current="true"]').count(), 1);
    }
    await context.close();
  }
  console.log('manecillas-input-modality-equivalence: OK');
} finally {
  await browser.close();
}
