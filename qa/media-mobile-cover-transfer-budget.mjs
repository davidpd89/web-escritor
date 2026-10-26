import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = (process.env.QA_ORIGIN || process.env.SITE_BASE_URL || 'http://127.0.0.1:4173').replace(/\/$/, '');
const routes = ['/libros/', '/libros/samuel-entre-mundos/', '/las-manecillas-del-recuerdo/'];
const LIMIT = 750 * 1024;
const browser = await chromium.launch({ headless: true });
try {
  for (const route of routes) {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, serviceWorkers: 'block' });
    const page = await context.newPage();
    const sizes = new Map();
    page.on('response', async response => {
      if (response.request().resourceType() !== 'image') return;
      if (new URL(response.url()).origin !== new URL(BASE).origin) return;
      try {
        const body = await response.body();
        sizes.set(response.url(), body.byteLength);
      } catch (error) {
        sizes.set(response.url(), -1);
      }
    });
    try {
      const response = await page.goto(BASE + route, { waitUntil: 'load' });
      assert.equal(response?.status(), 200, `${route}: HTTP ${response?.status()}`);
      const images = await page.locator('main img').evaluateAll(elements => elements.filter(img => {
        const r = img.getBoundingClientRect();
        const s = getComputedStyle(img);
        return r.width > 0 && r.height > 0 && r.top < innerHeight && r.bottom > 0 && s.display !== 'none' && s.visibility !== 'hidden';
      }).map(img => img.currentSrc || img.src));
      for (const src of images) {
        if (new URL(src).origin !== new URL(BASE).origin) continue;
        const bytes = sizes.get(src);
        assert.ok(Number.isInteger(bytes) && bytes > 0, `${route}: imagen ${src} sin transferencia válida: ${bytes}`);
        assert.ok(bytes <= LIMIT, `${route}: imagen ${src} pesa ${bytes} bytes; presupuesto ${LIMIT} bytes`);
      }
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}
console.log('PASS media-mobile-cover-transfer-budget');
