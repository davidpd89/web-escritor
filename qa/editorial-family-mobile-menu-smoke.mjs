import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const routes = ['/libros/', '/recomendaciones/', '/editoriales/'];
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
      const trigger = page.locator('[data-explore-open]');
      const dialog = page.locator('[data-explore-dialog]');
      await trigger.waitFor({ state: 'visible' });
      const bounds = await trigger.boundingBox();
      assert(bounds && bounds.width >= 24 && bounds.height >= 24, `${route} @ ${width}px: disparador demasiado pequeño`);
      assert(bounds.x >= -1 && bounds.x + bounds.width <= width + 1, `${route} @ ${width}px: disparador cortado`);
      await trigger.click();
      await dialog.waitFor({ state: 'visible' });
      assert(await dialog.evaluate(el => el.open), `${route} @ ${width}px: diálogo no abierto`);
      assert(await dialog.locator('a[href]:visible').count() > 0, `${route} @ ${width}px: menú sin enlaces visibles`);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      assert(overflow <= 1, `${route} @ ${width}px: menú provoca desbordamiento ${overflow}px`);
      await page.keyboard.press('Escape');
      await dialog.waitFor({ state: 'hidden' });
      assert(await trigger.isVisible(), `${route} @ ${width}px: disparador inaccesible tras cerrar`);
      assert.deepEqual(errors, [], `${route} @ ${width}px: errores JavaScript`);
      page.removeAllListeners('pageerror');
    }
    await context.close();
  }
} finally {
  await browser.close();
}
