import assert from 'node:assert/strict';
import { chromium, firefox, webkit } from 'playwright';

const O = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const WEEK = 7 * 24 * 60 * 60 * 1000;

for (const [name, engine] of Object.entries({ chromium, firefox, webkit })) {
  const browser = await engine.launch();
  try {
    for (const expired of [false, true]) {
      const context = await browser.newContext({ reducedMotion: 'reduce' });
      await context.route(/^https?:\/\//, r => r.request().url().startsWith(O) ? r.continue() : r.abort());
      await context.addInitScript(age => {
        if (localStorage.getItem('nl-popup-ts') === null) {
        localStorage.setItem('nl-popup-ts', String(Date.now() - age));
      }
      }, expired ? WEEK + 10000 : 1000);
      const page = await context.newPage();
      await page.goto(`${O}/universo/noveris/`, { waitUntil: 'load' });
      await page.evaluate(() => { scrollTo(0, document.documentElement.scrollHeight); dispatchEvent(new Event('scroll')); });
      const popup = page.locator('#nl-popup-dialog');
      if (expired) {
        await popup.waitFor({ state: 'visible', timeout: 4000 });
        await popup.locator('#nl-popup-skip').click();
        await popup.waitFor({ state: 'detached' });
        const ts = await page.evaluate(() => Number(localStorage.getItem('nl-popup-ts')));
        assert.ok(Math.abs(Date.now() - ts) < 10000, `${name}: descarte no renovó cooldown`);
      } else {
        await page.waitForTimeout(350);
        assert.equal(await popup.count(), 0, `${name}: popup prematuro`);
      }
      await page.goto(`${O}/cuaderno/`, { waitUntil: 'load' });
      await page.evaluate(() => { scrollTo(0, document.documentElement.scrollHeight); dispatchEvent(new Event('scroll')); });
      await page.waitForTimeout(250);
      assert.equal(await page.locator('#nl-popup-dialog').count(), 0, `${name}: popup reaparece entre familias`);
      await context.close();
    }
    console.log(`PASS ${name}: popup cooldown`);
  } finally {
    await browser.close();
  }
}
