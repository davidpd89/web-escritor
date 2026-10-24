import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const routes = [
  'que-es-el-portal-fantasy', 'portal-fantasy-vs-fantasia-epica',
  'fantasia-juvenil-espanola-portales-magia-coste',
  'libros-fantasia-juvenil-espanola-2025-2026',
  'worldbuilding-noveris-ciudad-magica',
  'feria-libro-madrid-2026-samuel-entre-mundos',
  'sistema-de-magia-noveris'
];
const browser = await chromium.launch({ headless: true });
try {
  for (const slug of routes) for (const modality of ['keyboard', 'touch']) {
    const route = `/cuaderno/${slug}/`;
    const context = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: modality === 'touch', isMobile: modality === 'touch' });
    await context.route('**/*', r => new URL(r.request().url()).origin === new URL(BASE).origin ? r.continue() : r.abort());
    await context.addInitScript(() => {
      localStorage.setItem('nl-popup-ts', String(Date.now()));
      window.__shares = [];
      Object.defineProperty(navigator, 'share', { configurable: true, value: async value => { window.__shares.push(value); } });
    });
    const page = await context.newPage();
    try {
      await page.goto(BASE + route);
      const button = page.locator('[data-share-url]');
      assert.equal(await button.count(), 1, route);
      if (modality === 'keyboard') {
        await button.focus();
        await page.keyboard.press('Enter');
      } else await button.tap();
      await page.waitForFunction(() => window.__shares.length === 1);
      const shares = await page.evaluate(() => window.__shares);
      assert.equal(shares.length, 1, `${route} ${modality}: invocación duplicada`);
      assert.equal(shares[0].url, `https://davidportodiaz.com${route}`);
      assert.ok(shares[0].title?.trim());
      assert.match(await page.locator('#article-share-status').innerText(), /Compartido/);
    } finally { await context.close(); }
  }
  console.log('PASS cuaderno share modality matrix');
} finally { await browser.close(); }
