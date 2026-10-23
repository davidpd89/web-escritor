import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const JOURNEYS = [
  ['/autor.html', '/herramientas/'],
  ['/herramientas/', '/prensa.html'],
  ['/prensa.html', '/recomendaciones/'],
  ['/libros/', '/autor.html'],
];
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  for (const width of [390, 1280]) {
    const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: 'reduce', serviceWorkers: 'block' });
    await context.route('**/*', route => new URL(route.request().url()).origin === ORIGIN ? route.continue() : route.abort());
    await context.addInitScript(() => { sessionStorage.setItem('dp-intro-seen', '1'); localStorage.setItem('nl-popup-ts', String(Date.now())); });
    const page = await context.newPage();
    page.setDefaultTimeout(10000);
    for (const [source, target] of JOURNEYS) {
      const errors = [];
      const onError = error => errors.push(error.message);
      page.on('pageerror', onError);
      await page.goto(ORIGIN + source, { waitUntil: 'domcontentloaded' });
      const before = page.url();
      await page.locator('[data-explore-open]').first().click();
      await page.locator(`[data-explore-dialog] .explore-row[href="${target}"]`).click();
      await page.waitForURL(url => url.pathname === target);
      assert.ok((await page.locator('main h1').first().innerText()).trim(), target);
      await page.goBack({ waitUntil: 'domcontentloaded' });
      assert.equal(page.url(), before);
      await page.goForward({ waitUntil: 'domcontentloaded' });
      assert.equal(new URL(page.url()).pathname, target);
      assert.deepEqual(errors, [], `${width}px ${source} -> ${target}`);
      page.off('pageerror', onError);
    }
    await context.close();
  }
} finally {
  await browser.close();
}
console.log('PASS navigation nonreading history roundtrips');