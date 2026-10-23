import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const SOURCES = ['/autor.html', '/cuaderno/', '/herramientas/', '/editoriales/', '/las-manecillas-del-recuerdo/fragmentos/'];
const ACTIONS = [
  ['.header-home', '/', ''],
  ['.header-sitemap', '/mapa-del-sitio/', ''],
  ['.header-contact', '/prensa.html', '#contacto'],
];
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, reducedMotion: 'reduce', serviceWorkers: 'block' });
  await context.route('**/*', route => new URL(route.request().url()).origin === ORIGIN ? route.continue() : route.abort());
  await context.addInitScript(() => { sessionStorage.setItem('dp-intro-seen', '1'); localStorage.setItem('nl-popup-ts', String(Date.now())); });
  const page = await context.newPage();
  for (const source of SOURCES) {
    for (const [selector, path, hash] of ACTIONS) {
      await page.goto(ORIGIN + source, { waitUntil: 'domcontentloaded' });
      const link = page.locator(`header.site-header a${selector}`).first();
      assert.equal(await link.count(), 1, `${source}: missing ${selector}`);
      await link.click();
      await page.waitForURL(url => url.pathname === path && url.hash === hash);
      assert.ok((await page.locator('main h1').first().innerText()).trim(), `${source} -> ${path}`);
      if (hash) assert.equal(await page.locator(hash).count(), 1, `${hash}: nonexistent target`);
    }
  }
  await context.close();
} finally {
  await browser.close();
}
console.log('PASS header quick-action navigation');