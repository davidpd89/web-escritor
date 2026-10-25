import { chromium } from 'playwright';
import assert from 'node:assert/strict';

const BASE = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch({headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});
try {
  for (const path of ['/libros/', '/recomendaciones/', '/editoriales/']) {
    for (const width of [320, 390, 768, 1440]) {
      const page = await browser.newPage({viewport: {width, height: 900}, reducedMotion: 'reduce'});
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      const response = await page.goto(BASE + path, {waitUntil: 'load'});
      assert.equal(response?.status(), 200, `${path} HTTP`);
      await page.locator('main').first().waitFor({state: 'visible'});
      await page.evaluate(async () => { await document.fonts.ready; });
      const result = await page.evaluate(() => ({viewport: innerWidth, scroll: document.documentElement.scrollWidth, main: document.querySelector('main')?.getBoundingClientRect().width}));
      assert(result.scroll <= result.viewport + 1, `${path} desborda ${width}px: ${JSON.stringify(result)}`);
      assert(result.main > 0, `${path} sin contenido principal visible`);
      assert.deepEqual(errors, [], `${path} errores JS en ${width}px`);
      await page.close();
    }
  }
} finally {
  await browser.close();
}