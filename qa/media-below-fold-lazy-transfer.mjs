import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = (process.env.QA_ORIGIN || process.env.SITE_BASE_URL || 'http://127.0.0.1:4173').replace(/\/$/, '');
const routes = ['/libros/', '/libros/samuel-entre-mundos/', '/las-manecillas-del-recuerdo/'];
const browser = await chromium.launch({ headless: true });
let inspected = 0;
try {
  for (const route of routes) {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 }, serviceWorkers: 'block' });
    const page = await context.newPage();
    const requested = new Set();
    page.on('request', request => {
      if (request.resourceType() === 'image') requested.add(request.url());
    });
    try {
      const response = await page.goto(BASE + route, { waitUntil: 'load' });
      assert.equal(response?.status(), 200, `${route}: HTTP ${response?.status()}`);
      const candidates = await page.evaluate(() => [...document.images].filter(img => {
        const r = img.getBoundingClientRect();
        const s = getComputedStyle(img);
        return img.loading === 'lazy' && r.top > innerHeight * 3 && r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden';
      }).map(img => ({ src: img.currentSrc || img.src, top: img.getBoundingClientRect().top })));
      for (const candidate of candidates) {
        if (new URL(candidate.src).origin !== new URL(BASE).origin) continue;
        inspected++;
        assert.ok(!requested.has(candidate.src), `${route}: imagen lazy descargada prematuramente: ${candidate.src}, top=${candidate.top}px`);
      }
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}
console.log(`PASS media-below-fold-lazy-transfer: ${inspected} imágenes elegibles`);
