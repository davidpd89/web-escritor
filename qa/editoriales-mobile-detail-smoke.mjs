import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const routes = ['/editoriales/minotauro/', '/editoriales/nocturna-ediciones/', '/editoriales/duermevela-ediciones/'];
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

try {
  for (const width of [320, 360, 390]) {
    const context = await browser.newContext({ viewport: { width, height: 800 }, reducedMotion: 'reduce', serviceWorkers: 'block' });
    const page = await context.newPage();
    for (const route of routes) {
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      const response = await page.goto(`${BASE}${route}`, { waitUntil: 'domcontentloaded' });
      assert(response?.ok(), `${route} @ ${width}px: HTTP ${response?.status()}`);
      await page.locator('main h1').first().waitFor({ state: 'visible' });
      assert((await page.locator('main h1').first().innerText()).trim(), `${route} @ ${width}px: encabezado vacío`);
      await page.evaluate(() => document.fonts?.ready);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      assert(overflow <= 1, `${route} @ ${width}px: desbordamiento horizontal ${overflow}px`);
      const links = page.locator('main a[href]:visible');
      assert(await links.count() > 0, `${route} @ ${width}px: no hay enlaces principales utilizables`);
      for (let i = 0; i < await links.count(); i++) {
        const link = links.nth(i);
        await link.scrollIntoViewIfNeeded();
        await link.focus();
        const state = await link.evaluate(el => {
          const r = el.getBoundingClientRect();
          return { focused: document.activeElement === el, left: r.left, right: r.right, width: r.width };
        });
        assert(state.focused, `${route} @ ${width}px: enlace ${i} no recibe foco`);
        assert(state.width > 0 && state.left >= -1 && state.right <= width + 1, `${route} @ ${width}px: enlace ${i} fuera de pantalla: ${JSON.stringify(state)}`);
      }
      assert.deepEqual(errors, [], `${route} @ ${width}px: errores JavaScript`);
      page.removeAllListeners('pageerror');
    }
    await context.close();
  }
} finally {
  await browser.close();
}
