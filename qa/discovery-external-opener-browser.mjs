import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || process.env.QA_BASE_URL || 'http://127.0.0.1:4173').replace(/\/$/, '');
const ROUTES = ['/recomendaciones/', '/cuaderno/', '/herramientas/', '/editoriales/', '/libros/'];
const browser = await chromium.launch({
  headless: true,
  ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}),
});

try {
  const context = await browser.newContext({ reducedMotion: 'reduce' });
  for (const route of ROUTES) {
    const page = await context.newPage();
    const response = await page.goto(ORIGIN + route, { waitUntil: 'domcontentloaded', timeout: 25000 });
    assert.ok(response?.ok(), `${route}: HTTP ${response?.status()}`);
    await page.locator('main').waitFor({ state: 'attached' });
    const failures = await page.evaluate(() => {
      const failures = [];
      const base = location.origin;
      for (const a of document.querySelectorAll('a[href][target]')) {
        if (a.target.toLowerCase() !== '_blank') continue;
        let url;
        try { url = new URL(a.href, document.baseURI); } catch { continue; }
        if (!['http:', 'https:'].includes(url.protocol) || url.origin === base) continue;
        const rel = new Set(a.rel.toLowerCase().split(/\s+/));
        if (!rel.has('noopener') && !rel.has('noreferrer')) {
          failures.push({ href: a.href, rel: a.rel });
        }
      }
      return failures;
    });
    assert.deepEqual(failures, [], `${route}: enlaces externos target=_blank sin aislamiento: ${JSON.stringify(failures)}`);
    await page.close();
  }
  await context.close();
} finally {
  await browser.close();
}
console.log('PASS discovery external opener isolation');
