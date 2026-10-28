import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const ROUTE = '/donde-empieza-la-jaula/';
const browser = await chromium.launch({ headless: true });

try {
  for (const width of [360, 768, 1440]) {
    const context = await browser.newContext({ viewport: { width, height: 900 } });
    const page = await context.newPage();
    const failures = [];

    page.on('response', response => {
      const url = new URL(response.url());
      if (url.origin !== ORIGIN) return;
      if (!/\.(?:css|js)(?:\?|$)/i.test(url.pathname)) return;
      if (response.status() >= 400) failures.push(`${url.pathname}: HTTP ${response.status()}`);
    });
    page.on('requestfailed', request => {
      const url = new URL(request.url());
      if (url.origin === ORIGIN && /\.(?:css|js)$/i.test(url.pathname)) {
        failures.push(`${url.pathname}: ${request.failure()?.errorText}`);
      }
    });

    const response = await page.goto(`${ORIGIN}${ROUTE}`, { waitUntil: 'load' });
    assert.equal(response?.status(), 200, `${ROUTE} ${width}px: HTML inaccesible`);
    await page.evaluate(() => document.fonts.ready);

    const metrics = await page.evaluate(() => {
      const title = document.querySelector('.book-hero h1');
      const excerpt = document.querySelector('.excerpt-field');
      assertElement(title, 'h1');
      assertElement(excerpt, 'excerpt');
      function assertElement(el, name) {
        if (!el) throw new Error(`Elemento ausente: ${name}`);
      }
      const heading = getComputedStyle(title);
      const prose = getComputedStyle(excerpt);
      return {
        titleSize: parseFloat(heading.fontSize),
        proseSize: parseFloat(prose.fontSize),
        proseLineHeight: parseFloat(prose.lineHeight),
        titleVisible: title.getBoundingClientRect().width > 0 && heading.visibility === 'visible',
        overflow: document.documentElement.scrollWidth - innerWidth
      };
    });

    assert.deepEqual(failures, [], `${ROUTE} ${width}px: recursos fallidos`);
    assert.ok(metrics.titleVisible, `${ROUTE} ${width}px: título invisible`);
    assert.ok(metrics.titleSize >= 24, `${ROUTE} ${width}px: título ${metrics.titleSize}px`);
    assert.ok(metrics.proseSize >= 16, `${ROUTE} ${width}px: texto ${metrics.proseSize}px`);
    assert.ok(metrics.proseLineHeight >= metrics.proseSize * 1.35, `${ROUTE} ${width}px: interlineado insuficiente`);
    assert.ok(metrics.overflow <= 1, `${ROUTE} ${width}px: overflow ${metrics.overflow}px`);
    await context.close();
  }
  console.log('OK jaula critical resource visual');
} finally {
  await browser.close();
}
