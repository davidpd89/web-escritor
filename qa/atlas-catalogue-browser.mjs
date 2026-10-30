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
    // El recuento del estado es el total de coincidencias; en pantalla se muestran de 24 en 24.
    const visible = async () => parseInt(await page.locator('[data-atlas-count]').innerText(), 10);
    const rendered = () => page.locator('[data-atlas-card]:not([hidden])').count();
    const total = await visible();
    assert.ok(total >= 40, `${width}: catálogo con ${total} entradas`);
    assert.equal(await rendered(), Math.min(total, 24), `${width}: primera página`);
    if (total > 24) {
      await page.locator('[data-atlas-more]').click();
      assert.equal(await rendered(), Math.min(total, 48), `${width}: mostrar más`);
    }

    await page.locator('input[data-facet="pais"][value="IE"]').check();
    const ireland = await visible();
    assert.ok(ireland > 0 && ireland < total, `${width}: filtro de país`);
    await page.locator('input[data-facet="tipo"][value="library"]').check();
    const irelandLibraries = await visible();
    assert.ok(irelandLibraries >= 1 && irelandLibraries < ireland, `${width}: filtros combinados`);
    assert.ok(page.url().includes('pais=IE') && page.url().includes('tipo=library'), `${width}: estado en la URL`);

    await page.getByRole('button', { name: 'Restablecer' }).click();
    await page.waitForFunction((n) => parseInt(document.querySelector('[data-atlas-count]').textContent, 10) === n, total);
    assert.equal(await visible(), total, `${width}: restablecer`);

    await page.locator('input[data-filter="q"]').fill('pessoa');
    const found = await visible();
    assert.ok(found >= 1 && found < total, `${width}: búsqueda`);
    await page.locator('input[data-filter="q"]').fill('zzzz-sin-resultados');
    assert.equal(await visible(), 0);
    assert.equal(await page.locator('[data-atlas-empty]').isVisible(), true, `${width}: estado vacío`);
    await page.getByRole('button', { name: 'Restablecer' }).click();
    await page.waitForFunction((n) => parseInt(document.querySelector('[data-atlas-count]').textContent, 10) === n, total);

    // Estado compartible: abrir con filtros en la URL.
    await page.goto(`${BASE}/atlas-literario/?autor=james-joyce`);
    await page.waitForSelector('[data-atlas-filters] fieldset:not([disabled])');
    assert.ok((await visible()) >= 2, `${width}: filtros desde la URL`);
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `${width}: sin desborde`);
    assert.deepEqual(errors, [], `${width}: sin errores de consola`);
    await context.close();
  }
  // Teclado: «Mostrar más» con foco + Enter lleva el foco a la primera entrada
  // nueva (nunca a BODY), en la última tanda y en una intermedia (fixture).
  const focusInfo = (page) => page.evaluate(() => {
    const el = document.activeElement;
    const card = el && el.closest('[data-atlas-card]');
    const cards = Array.from(document.querySelectorAll('[data-atlas-card]'));
    return {
      tag: el ? el.tagName : null,
      cardIndex: card ? cards.indexOf(card) : -1,
      visible: Boolean(el && el.getClientRects().length),
      buttonVisible: !document.querySelector('[data-atlas-more-wrap]').hidden,
      status: document.querySelector('[data-atlas-count]').textContent,
    };
  });
  for (const width of [390, 1280]) {
    const context = await browser.newContext({ viewport: { width, height: 900 } });
    await context.addInitScript(() => { try { localStorage.setItem('nl-popup-ts', String(Date.now())); } catch {} });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.message));
    await page.goto(`${BASE}/atlas-literario/`);
    await page.waitForSelector('[data-atlas-filters] fieldset:not([disabled])');
    const total = await page.locator('[data-atlas-card]').count();
    assert.ok(total > 24 && total <= 48, `${width}: el catálogo real cabe en dos tandas (${total})`);
    await page.locator('[data-atlas-more]').focus();
    await page.keyboard.press('Enter');
    let info = await focusInfo(page);
    assert.equal(info.tag, 'A', `${width}: última tanda, foco en un enlace (${info.tag})`);
    assert.equal(info.cardIndex, 24, `${width}: última tanda, foco en la primera entrada nueva`);
    assert.ok(info.visible && !info.buttonVisible, `${width}: destino visible y botón retirado`);
    assert.match(info.status, /se muestran todos/, `${width}: anuncio de la ampliación`);
    await page.keyboard.press('Tab');
    info = await focusInfo(page);
    assert.notEqual(info.tag, 'BODY', `${width}: el siguiente Tab sigue en el contenido`);

    // Restablecer por teclado no deja el foco en el botón deshabilitado.
    await page.locator('input[data-facet="pais"][value="IE"]').check();
    assert.equal(await page.locator('[data-atlas-more-wrap]').isHidden(), true, `${width}: total <= 24 sin botón`);
    await page.getByRole('button', { name: 'Restablecer' }).focus();
    await page.keyboard.press('Enter');
    await page.waitForFunction(() => document.querySelector('button[type="reset"]').disabled);
    assert.equal(await page.evaluate(() => document.activeElement.matches('input[data-filter="q"]')), true, `${width}: foco tras restablecer`);
    await context.close();

    // Fixture con el triple de entradas: tanda intermedia con el botón presente.
    const fixture = await browser.newContext({ viewport: { width, height: 900 } });
    await fixture.addInitScript(() => { try { localStorage.setItem('nl-popup-ts', String(Date.now())); } catch {} });
    await fixture.route(/\/assets\/atlas-catalogue\.js/, async (route) => {
      const response = await route.fetch();
      const clone = "document.querySelectorAll('[data-atlas-card]').forEach(function (c) { c.parentNode.appendChild(c.cloneNode(true)); c.parentNode.appendChild(c.cloneNode(true)); });\n";
      await route.fulfill({ response, body: clone + (await response.text()) });
    });
    const big = await fixture.newPage();
    big.on('pageerror', (e) => errors.push(e.message));
    await big.goto(`${BASE}/atlas-literario/`);
    await big.waitForSelector('[data-atlas-filters] fieldset:not([disabled])');
    const bigTotal = await big.locator('[data-atlas-card]').count();
    await big.locator('[data-atlas-more]').focus();
    await big.keyboard.press('Enter');
    info = await focusInfo(big);
    assert.equal(info.cardIndex, 24, `${width}: tanda intermedia, foco en la entrada 25`);
    assert.ok(info.buttonVisible, `${width}: tanda intermedia conserva el botón`);
    assert.equal(info.status, `${bigTotal} resultados · se muestran 48`, `${width}: anuncio intermedio`);
    // Puntero: el clic sigue el mismo criterio.
    await big.locator('[data-atlas-more]').click();
    info = await focusInfo(big);
    assert.equal(info.cardIndex, 48, `${width}: clic, foco en la entrada 49`);
    assert.ok(await big.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `${width}: sin desborde`);
    assert.deepEqual(errors, [], `${width}: sin errores de consola (teclado)`);
    await fixture.close();
  }

  const nojs = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 390, height: 900 } });
  const page = await nojs.newPage();
  await page.goto(`${BASE}/atlas-literario/`);
  assert.ok((await page.locator('[data-atlas-card]:visible').count()) >= 40, 'sin JS se ven todas las entradas');
  await nojs.close();
  console.log('PASS atlas catalogue: filtros, búsqueda, URL, restablecer, vacío, teclado en Mostrar más y sin JS');
} finally {
  await browser.close();
}
