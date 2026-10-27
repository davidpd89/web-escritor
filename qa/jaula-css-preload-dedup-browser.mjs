import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const ROUTE = '/donde-empieza-la-jaula/';
const browser = await chromium.launch({ headless: true });

try {
  for (const width of [390, 1440]) {
    const context = await browser.newContext({ viewport: { width, height: 900 } });
    const page = await context.newPage();
    const requests = new Map();

    page.on('request', request => {
      const url = new URL(request.url());
      if (url.origin !== ORIGIN || !url.pathname.endsWith('.css')) return;
      requests.set(request.url(), (requests.get(request.url()) || 0) + 1);
    });

    const response = await page.goto(`${ORIGIN}${ROUTE}`, { waitUntil: 'load' });
    assert.equal(response?.status(), 200, `${ROUTE} ${width}px: página inaccesible`);
    await page.evaluate(() => document.fonts.ready);

    const duplicates = [...requests].filter(([, count]) => count > 1);
    assert.deepEqual(duplicates, [], `${ROUTE} ${width}px: CSS solicitado varias veces`);

    const result = await page.evaluate(() => {
      const excerpt = document.querySelector('.excerpt-field');
      if (!excerpt) throw new Error('Falta el capítulo');
      const css = getComputedStyle(excerpt);
      return {
        fontSize: parseFloat(css.fontSize),
        lineHeight: parseFloat(css.lineHeight),
        display: css.display,
        stylesheets: [...document.styleSheets].length
      };
    });

    assert.ok(requests.size > 0, `${ROUTE} ${width}px: ninguna hoja CSS solicitada`);
    assert.ok(result.stylesheets > 0, `${ROUTE} ${width}px: sin hojas de estilo`);
    assert.ok(result.fontSize >= 16, `${ROUTE} ${width}px: texto ${result.fontSize}px`);
    assert.ok(result.lineHeight >= result.fontSize * 1.35, `${ROUTE} ${width}px: interlineado ${result.lineHeight}px`);
    await context.close();
  }
  console.log('OK jaula CSS preload dedup');
} finally {
  await browser.close();
}
