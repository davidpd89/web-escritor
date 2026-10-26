import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = (process.env.QA_ORIGIN || process.env.SITE_BASE_URL || 'http://127.0.0.1:4173').replace(/\/$/, '');
const routes = ['/libros/', '/libros/samuel-entre-mundos/', '/las-manecillas-del-recuerdo/'];
const browser = await chromium.launch({ headless: true });
try {
  for (const route of routes) {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await context.newPage();
    const transfers = new Map();
    page.on('response', response => {
      const url = new URL(response.url());
      if (url.origin !== new URL(BASE).origin || !url.pathname.endsWith('.css')) return;
      if (response.status() === 304 || response.fromServiceWorker()) return;
      const key = url.pathname + url.search;
      transfers.set(key, (transfers.get(key) || 0) + 1);
    });
    try {
      const response = await page.goto(BASE + route, { waitUntil: 'load' });
      assert.equal(response?.status(), 200, `${route}: HTTP ${response?.status()}`);
      const duplicates = [...transfers].filter(([, count]) => count > 1);
      assert.deepEqual(duplicates, [], `${route}: hojas CSS descargadas varias veces: ${JSON.stringify(duplicates)}`);
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}
console.log('PASS media-css-request-deduplication');
