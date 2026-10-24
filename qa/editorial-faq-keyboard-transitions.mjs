import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const routes = ['/cuaderno/que-es-el-portal-fantasy/', '/cuaderno/portal-fantasy-vs-fantasia-epica/', '/universo/noveris/'];
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  for (const route of routes) {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
    await context.route('**/*', r => new URL(r.request().url()).origin === BASE ? r.continue() : r.abort());
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    const response = await page.goto(BASE + route, { waitUntil: 'domcontentloaded' });
    assert.ok(response?.ok(), `${route}: carga fallida`);
    const details = page.locator('main details');
    assert.ok(await details.count() >= 3, `${route}: faltan detalles interactivos`);
    for (let i = 0; i < await details.count(); i++) {
      const detail = details.nth(i);
      const summary = detail.locator('summary');
      await summary.focus();
      assert.ok(await summary.evaluate(el => el === document.activeElement), `${route}: summary sin foco`);
      const before = await detail.evaluate(el => el.open);
      await page.keyboard.press('Enter');
      assert.equal(await detail.evaluate(el => el.open), !before, `${route}: Enter no alterna`);
      await page.keyboard.press('Space');
      assert.equal(await detail.evaluate(el => el.open), before, `${route}: Espacio no alterna`);
    }
    assert.deepEqual(errors, [], `${route}: errores de página`);
    await context.close();
  }
} finally { await browser.close(); }
console.log('OK: FAQ accesibles por teclado');
