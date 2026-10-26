import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await page.goto(`${ORIGIN}/editoriales/`, { waitUntil: 'domcontentloaded' });
  const firstName = await page.locator('[data-editorial-card]').first().getAttribute('data-name');
  assert.ok(firstName, '/editoriales/: no hay editorial para búsqueda compartible');
  await page.locator('[data-editoriales-search]').fill(firstName);
  await page.waitForFunction(name => location.hash.includes('q=') && document.querySelector('[data-editoriales-search]').value === name, firstName);
  const shared = page.url();
  await page.goto(shared, { waitUntil: 'domcontentloaded' });
  await page.evaluate(() => {
    window.__qaShifts = 0;
    window.__qaObserver = new PerformanceObserver(list => {
      for (const entry of list.getEntries()) {
        if (!entry.hadRecentInput) window.__qaShifts += entry.value;
      }
    });
    window.__qaObserver.observe({ type: 'layout-shift', buffered: true });
  });
  await page.waitForFunction(name => {
    const search = document.querySelector('[data-editoriales-search]');
    const visible = document.querySelectorAll('[data-editorial-card]:not([hidden])');
    return search?.value === name && visible.length > 0;
  }, firstName);
  await page.evaluate(() => document.fonts.ready);
  const result = await page.evaluate(() => ({
    cls: window.__qaShifts,
    overflow: document.documentElement.scrollWidth - innerWidth,
    count: document.querySelectorAll('[data-editorial-card]:not([hidden])').length
  }));
  assert.ok(result.cls < 0.05, `/editoriales/: CLS al restaurar ${shared}: ${result.cls}`);
  assert.ok(result.overflow <= 1, `/editoriales/: desbordamiento móvil ${result.overflow}px`);
  assert.ok(result.count > 0, `/editoriales/: URL compartida sin resultados: ${shared}`);
  console.log('editoriales-shared-filter-cls: PASS');
} finally {
  await browser.close();
}