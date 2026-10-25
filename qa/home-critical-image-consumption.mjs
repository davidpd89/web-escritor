import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:8000';
const target = '/assets/manecillas-del-recuerdo-3d-transparent.webp';
const browser = await chromium.launch({ headless: true });

try {
  const context = await browser.newContext({ serviceWorkers: 'block' });
  await context.route(/^https?:\/\//, route => new URL(route.request().url()).origin === new URL(origin).origin ? route.continue() : route.abort());
  await context.addInitScript(() => sessionStorage.setItem('dp-intro-seen', '1'));
  const page = await context.newPage();
  try {
    const response = await page.goto(origin + '/', { waitUntil: 'load' });
    assert.equal(response.status(), 200, '/: HTTP inesperado');
    await page.waitForFunction(path => [...document.images].some(img => new URL(img.currentSrc || img.src).pathname === path && img.complete && img.naturalWidth > 0), target, { timeout: 15000 });
    const result = await page.evaluate(path => {
      const preloads = [...document.querySelectorAll('link[rel="preload"][as="image"]')].filter(link => new URL(link.href).pathname === path);
      const images = [...document.images].filter(img => new URL(img.currentSrc || img.src).pathname === path);
      const visible = images.filter(img => {
        const rect = img.getBoundingClientRect();
        const style = getComputedStyle(img);
        return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility === 'visible' && img.complete && img.naturalWidth > 0;
      });
      return { preloadCount: preloads.length, consumerCount: visible.length, widths: visible.map(img => img.naturalWidth) };
    }, target);
    assert.equal(result.preloadCount, 1, `/: ${target}: ${result.preloadCount} precargas`);
    assert.ok(result.consumerCount > 0, `/: ${target}: precarga sin consumidor visible y decodificado`);
  } finally {
    await context.close();
  }
} finally {
  await browser.close();
}
