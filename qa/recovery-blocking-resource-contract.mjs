import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:8000';
const browser = await chromium.launch({ headless: true });

try {
  for (const route of ['/offline.html', '/404.html']) {
    const context = await browser.newContext({ serviceWorkers: 'block' });
    await context.route(/^https?:\/\//, request => new URL(request.request().url()).origin === new URL(origin).origin ? request.continue() : request.abort());
    const page = await context.newPage();
    try {
      const response = await page.goto(new URL(route, origin).href, { waitUntil: 'load' });
      assert.equal(response.status(), 200, `${route}: HTTP inesperado`);
      const resources = await page.evaluate(() => {
        const scripts = [...document.querySelectorAll('script[src]')].filter(s => !s.defer && !s.async && s.type !== 'module').map(s => s.src);
        const styles = [...document.querySelectorAll('link[rel="stylesheet"]')].map(s => s.href);
        const title = document.querySelector('h1');
        return { scripts, styles, title: title?.textContent?.trim() || '' };
      });
      assert.ok(resources.title, `${route}: falta el título de recuperación`);
      assert.deepEqual(resources.scripts, [], `${route}: scripts externos bloqueantes: ${resources.scripts.join(', ')}`);
      if (route === '/offline.html') {
        assert.deepEqual(resources.styles, [], `${route}: dependencias CSS externas: ${resources.styles.join(', ')}`);
      }
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}
