// QA del catálogo del Atlas: filtros combinados, búsqueda, restablecer, URL y sin JS.
import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  for (const width of [390, 1280]) {
    const context = await browser.newContext({ viewport: { width, height: 900 } });
    await context.addInitScript(() => { try { localStorage.setItem('nl-popup-ts', String(Date.now())); } catch {} });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.message));
    await page.goto(`${BASE}/atlas-literario/`);
    await page.waitForSelector('[data-atlas-filters] fieldset:not([disabled])');
    const visible = () => page.locator('[data-atlas-card]:not([hidden])').count();
    const total = await visible();
    assert.ok(total >= 40, `${width}: catálogo con ${total} entradas`);
    assert.match(await page.locator('[data-atlas-count]').innerText(), new RegExp(`^${total} resultados`));

    await page.locator('input[data-facet="pais"][value="IE"]').check();
    const ireland = await visible();
    assert.ok(ireland > 0 && ireland < total, `${width}: filtro de país`);
    await page.locator('input[data-facet="tipo"][value="library"]').check();
    const irelandLibraries = await visible();
    assert.ok(irelandLibraries >= 1 && irelandLibraries < ireland, `${width}: filtros combinados`);
    assert.ok(page.url().includes('pais=IE') && page.url().includes('tipo=library'), `${width}: estado en la URL`);

    await page.getByRole('button', { name: 'Restablecer' }).click();
    await page.waitForFunction((n) => document.querySelectorAll('[data-atlas-card]:not([hidden])').length === n, total);
    assert.equal(await visible(), total, `${width}: restablecer`);

    await page.locator('input[data-filter="q"]').fill('pessoa');
    const found = await visible();
    assert.ok(found >= 1 && found < total, `${width}: búsqueda`);
    await page.locator('input[data-filter="q"]').fill('zzzz-sin-resultados');
    assert.equal(await visible(), 0);
    assert.equal(await page.locator('[data-atlas-empty]').isVisible(), true, `${width}: estado vacío`);
    await page.getByRole('button', { name: 'Restablecer' }).click();
    await page.waitForFunction((n) => document.querySelectorAll('[data-atlas-card]:not([hidden])').length === n, total);

    // Estado compartible: abrir con filtros en la URL.
    await page.goto(`${BASE}/atlas-literario/?autor=james-joyce`);
    await page.waitForSelector('[data-atlas-filters] fieldset:not([disabled])');
    assert.ok((await visible()) >= 2, `${width}: filtros desde la URL`);
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `${width}: sin desborde`);
    assert.deepEqual(errors, [], `${width}: sin errores de consola`);
    await context.close();
  }
  const nojs = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 390, height: 900 } });
  const page = await nojs.newPage();
  await page.goto(`${BASE}/atlas-literario/`);
  assert.ok((await page.locator('[data-atlas-card]:visible').count()) >= 40, 'sin JS se ven todas las entradas');
  await nojs.close();
  console.log('PASS atlas catalogue: filtros, búsqueda, URL, restablecer, vacío y sin JS');
} finally {
  await browser.close();
}
