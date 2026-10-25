import assert from 'node:assert/strict';
import {chromium, firefox, webkit} from 'playwright';
const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
for (const [name, engine] of Object.entries({chromium, firefox, webkit})) {
  const browser = await engine.launch();
  try {
    const page = await browser.newPage({viewport: {width: 800, height: 600}, reducedMotion: 'reduce'});
    await page.route(/^https?:\/\/(?!127\.0\.0\.1)/, r => r.abort());
    try {
      await page.goto(origin + '/las-manecillas-del-recuerdo/fragmentos/', {waitUntil: 'domcontentloaded'});
      if (await page.locator('body[data-back-to-top]').count()) {
        assert.equal(await page.locator('.back-to-top').count(), 1);
        await page.evaluate(() => {window.__scrollCalls = []; const original = window.scrollTo.bind(window); window.scrollTo = (...args) => {window.__scrollCalls.push(args); return original(...args);}; window.scrollTo(0, 900);});
        await page.waitForFunction(() => scrollY > 500);
        await page.waitForFunction(() => document.querySelector('.back-to-top')?.classList.contains('is-visible'));
        await page.locator('.back-to-top').click();
        const calls = await page.evaluate(() => window.__scrollCalls);
        assert.ok(calls.some(args => args[0]?.top === 0 && args[0]?.behavior === 'auto'), `${name}: no respeta movimiento reducido`);
        await page.waitForFunction(() => scrollY < 5);
      }
    } finally {await page.close();}
  } finally {await browser.close();}
}
console.log('PASS back-to-top reduced motion');