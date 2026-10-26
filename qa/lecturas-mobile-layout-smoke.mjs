import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const route = '/lecturas/';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

try {
  for (const width of [320, 360, 390]) {
    const context = await browser.newContext({ viewport: { width, height: 800 }, reducedMotion: 'reduce', serviceWorkers: 'block' });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const response = await page.goto(`${BASE}${route}`, { waitUntil: 'domcontentloaded' });
    assert(response?.ok(), `${route} @ ${width}px: HTTP ${response?.status()}`);
    await page.locator('main h1').waitFor({ state: 'visible' });
    assert.match(await page.locator('main h1').innerText(), /Qué estoy leyendo/, `${route} @ ${width}px: encabezado incorrecto`);
    const cards = page.locator('.reading-card');
    assert(await cards.count() > 0, `${route} @ ${width}px: ninguna tarjeta de lectura`);
    await page.evaluate(() => document.fonts?.ready);
    for (let i = 0; i < await cards.count(); i++) {
      const card = cards.nth(i);
      await card.scrollIntoViewIfNeeded();
      const state = await card.evaluate(el => {
        const r = el.getBoundingClientRect();
        return { left: r.left, right: r.right, width: r.width, height: r.height, text: el.innerText.trim() };
      });
      assert(state.text.length > 0, `${route} @ ${width}px: tarjeta ${i} vacía`);
      assert(state.width > 0 && state.height > 0, `${route} @ ${width}px: tarjeta ${i} sin superficie visible`);
      assert(state.left >= -1 && state.right <= width + 1, `${route} @ ${width}px: tarjeta ${i} cortada: ${JSON.stringify(state)}`);
    }
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
    assert(overflow <= 1, `${route} @ ${width}px: desbordamiento horizontal ${overflow}px`);
    assert.deepEqual(errors, [], `${route} @ ${width}px: errores JavaScript`);
    await context.close();
  }
} finally {
  await browser.close();
}
