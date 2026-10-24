import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  for (const width of [320, 390, 1440]) {
    const context = await browser.newContext({ viewport: { width, height: 900 } });
    await context.route('**/*', route => route.request().url().startsWith(origin) ? route.continue() : route.abort());
    const page = await context.newPage();
    await page.goto(`${origin}/las-manecillas-del-recuerdo/fragmentos/`);
    const metrics = await page.locator('.excerpt-field').evaluateAll(fields => fields.map(field => {
      const paragraph = field.querySelector('p');
      const style = getComputedStyle(paragraph);
      const rect = field.getBoundingClientRect();
      const font = parseFloat(style.fontSize);
      const line = parseFloat(style.lineHeight);
      return { width: rect.width, font, ratio: line / font, clippedX: field.scrollWidth > field.clientWidth + 1, clippedY: field.scrollHeight > field.clientHeight + 1 };
    }));
    assert.equal(metrics.length, 3);
    for (const metric of metrics) {
      assert(metric.font >= 15.5, `${width}: letra demasiado pequeña`);
      assert(metric.ratio >= 1.4, `${width}: interlineado insuficiente`);
      assert(metric.width >= 200 && metric.width <= 850, `${width}: columna de lectura inadecuada (${metric.width})`);
      assert(!metric.clippedX && !metric.clippedY, `${width}: texto recortado`);
    }
    assert(Math.max(...metrics.map(m => m.font)) - Math.min(...metrics.map(m => m.font)) < 1);
    await context.close();
  }
  console.log('manecillas-reading-legibility: OK');
} finally {
  await browser.close();
}
