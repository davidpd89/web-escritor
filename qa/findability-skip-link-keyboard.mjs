import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

try {
  for (const route of ['/mapa-del-sitio/', '/empieza-aqui/']) {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(String(e)));
    await page.goto(BASE + route, { waitUntil: 'domcontentloaded' });
    await page.keyboard.press('Tab');
    const focused = await page.evaluate(() => ({ tag: document.activeElement?.tagName, href: document.activeElement?.getAttribute('href') }));
    assert.deepEqual(focused, { tag: 'A', href: '#contenido' }, `${route}: primer foco incorrecto`);
    await page.keyboard.press('Enter');
    await page.waitForFunction(() => location.hash === '#contenido');
    assert.equal(await page.evaluate(() => document.activeElement?.id), 'contenido', `${route}: el foco no llega a main`);
    assert.deepEqual(errors, [], `${route}: errores JavaScript`);
    await context.close();
  }
  console.log('findability-skip-link-keyboard: OK');
} finally {
  await browser.close();
}