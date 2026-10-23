import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const SOURCES = ['/autor.html', '/cuaderno/', '/herramientas/', '/mapa-del-sitio/'];
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce', serviceWorkers: 'block' });
  await context.route('**/*', route => new URL(route.request().url()).origin === ORIGIN ? route.continue() : route.abort());
  await context.addInitScript(() => { sessionStorage.setItem('dp-intro-seen', '1'); localStorage.setItem('nl-popup-ts', String(Date.now())); });
  const page = await context.newPage();
  for (const source of SOURCES) {
    const errors = [];
    const listener = e => errors.push(e.message);
    page.on('pageerror', listener);
    await page.goto(ORIGIN + source, { waitUntil: 'domcontentloaded' });
    const opener = page.locator('[data-explore-open]').first();
    const snapshot = () => page.locator('[data-explore-dialog] .explore-list a[href]').evaluateAll(items => items.map(a => a.getAttribute('href')));
    const initial = await snapshot();
    assert.ok(initial.length >= 5, `${source}: empty navigation`);
    const forms = await page.locator('[data-explore-dialog] form').count();
    for (let n = 0; n < 8; n++) {
      await opener.click();
      await page.waitForFunction(() => document.querySelector('[data-explore-dialog]')?.open === true);
      assert.deepEqual(await snapshot(), initial, `${source}: changed links at cycle ${n}`);
      await page.keyboard.press('Escape');
      await page.waitForFunction(() => document.querySelector('[data-explore-dialog]')?.open === false);
      assert.equal(await page.locator('[data-explore-dialog] form').count(), forms, `${source}: duplicated form`);
    }
    assert.deepEqual(errors, [], `${source}: accumulated JS errors`);
    page.off('pageerror', listener);
  }
  await context.close();
} finally {
  await browser.close();
}
console.log('PASS repeated Explore interactions');