import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  const context = await browser.newContext({ viewport: { width: 390, height: 900 }, reducedMotion: 'reduce' });
  await context.route('**/*', route => route.request().url().startsWith(origin) ? route.continue() : route.abort());
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(`${origin}/las-manecillas-del-recuerdo/fragmentos/`);
  const metrics = await page.evaluate(async () => {
    const index = document.querySelector('[data-fragment-index]');
    let changes = 0;
    let violations = 0;
    const observer = new MutationObserver(records => { changes += records.length; });
    observer.observe(index, { subtree: true, attributes: true, childList: true, characterData: true });
    const distance = document.documentElement.scrollHeight - innerHeight;
    for (let step = 0; step <= 24; step++) {
      scrollTo({ top: distance * step / 24, behavior: 'instant' });
      await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
      if (index.querySelectorAll('[data-fragment-link][data-current="true"]').length > 1) violations++;
    }
    await new Promise(resolve => setTimeout(resolve, 250));
    observer.disconnect();
    return { changes, violations };
  });
  assert.equal(metrics.violations, 0, 'Dos fragmentos simultáneamente activos');
  assert(metrics.changes <= 100, `Actualizaciones DOM excesivas: ${metrics.changes}`);
  assert.deepEqual(errors, []);
  console.log('manecillas-scroll-mutation-budget: OK', metrics);
  await context.close();
} finally {
  await browser.close();
}
