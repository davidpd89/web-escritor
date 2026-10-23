import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const TARGETS = ['/libros/', '/cuaderno/', '/herramientas/', '/fragmento/', '/editoriales/'];
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, javaScriptEnabled: false, serviceWorkers: 'block' });
  await context.route('**/*', route => new URL(route.request().url()).origin === ORIGIN ? route.continue() : route.abort());
  const page = await context.newPage();
  for (const target of TARGETS) {
    const response = await page.goto(ORIGIN + '/mapa-del-sitio/', { waitUntil: 'domcontentloaded' });
    assert.equal(response.status(), 200);
    const link = page.locator(`.findability-directory a[href="${target}"]`).first();
    assert.equal(await link.count(), 1, `Missing ${target}`);
    assert.ok(await link.isVisible(), `${target} hidden without JavaScript`);
    await link.click();
    await page.waitForURL(url => url.pathname === target);
    assert.ok((await page.locator('main h1').first().innerText()).trim(), `${target}: missing heading`);
    assert.ok((await page.locator('main').innerText()).trim().length > 100, `${target}: empty main`);
    await page.goBack({ waitUntil: 'domcontentloaded' });
    assert.equal(new URL(page.url()).pathname, '/mapa-del-sitio/');
  }
  await context.close();
} finally {
  await browser.close();
}
console.log('PASS no-JS sitemap journeys');