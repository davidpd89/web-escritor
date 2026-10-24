import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
try {
  for (const width of [390, 1280]) {
    const context = await browser.newContext({ viewport: { width, height: 900 } });
    await context.route('**/*', r => {
      const url = new URL(r.request().url());
      return url.origin === new URL(BASE).origin ? r.continue() : r.abort();
    });
    await context.addInitScript(() => localStorage.setItem('nl-popup-ts', String(Date.now())));
    const page = await context.newPage();
    try {
      await page.goto(BASE + '/cuaderno/');
      await page.locator('main a[href="/cuaderno/temas/fantasia-de-portales/"]').click();
      assert.equal(new URL(page.url()).pathname, '/cuaderno/temas/fantasia-de-portales/');
      assert.match(await page.locator('main h1').innerText(), /Fantasía de portales/);
      await page.locator('.cuaderno-topic-step h2 a').first().click();
      assert.equal(new URL(page.url()).pathname, '/cuaderno/que-es-el-portal-fantasy/');
      assert.match(await page.locator('main h1').innerText(), /portal fantasy/i);
      await page.goBack({ waitUntil: 'domcontentloaded' });
      assert.equal(await page.locator('.cuaderno-topic-step').count(), 3);
      await page.goBack({ waitUntil: 'domcontentloaded' });
      assert.equal(new URL(page.url()).pathname, '/cuaderno/');
      assert.ok(await page.locator('.cuaderno-feature h2 a').count() === 1);
      await page.goForward({ waitUntil: 'domcontentloaded' });
      assert.equal(new URL(page.url()).pathname, '/cuaderno/temas/fantasia-de-portales/');
      assert.equal(await page.locator('main h1').isVisible(), true);
    } finally { await context.close(); }
  }
  console.log('PASS cuaderno topic reader journey');
} finally { await browser.close(); }
