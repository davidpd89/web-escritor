import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.SITE_ORIGIN;
assert.ok(origin, 'SITE_ORIGIN debe apuntar al servidor local del repositorio');
const site = new URL(origin).origin;
const route = '/cuaderno/que-es-el-portal-fantasy/';
const browser = await chromium.launch({ headless: true });

async function openPage(initScript) {
  const context = await browser.newContext({ viewport: { width: 320, height: 900 } });
  await context.route('**/*', request => {
    if (new URL(request.request().url()).origin === site) return request.continue();
    return request.abort();
  });
  await context.addInitScript(initScript);
  const page = await context.newPage();
  const response = await page.goto(new URL(route, site).href, { waitUntil: 'networkidle' });
  assert.equal(response?.status(), 200, 'artículo accesible en servidor local');
  return { context, page };
}

async function checkManual(page, expected) {
  await page.waitForFunction(value => {
    const input = document.querySelector('.article-utilities input.article-share-manual');
    return input && !input.hidden && input.value === value && document.querySelector('#article-share-status')?.textContent === 'No se pudo copiar automáticamente. Selecciona el enlace para copiarlo';
  }, expected);
  const input = page.locator('.article-utilities input.article-share-manual');
  assert.equal(await input.count(), 1, 'debe existir un solo campo manual');
  assert.equal(await input.inputValue(), expected, 'valor tomado de data-share-url');
  assert.equal(await input.evaluate(el => el.readOnly), true, 'campo de solo lectura');
  assert.equal(await page.getByRole('textbox', { name: 'Enlace del artículo para copiar' }).count(), 1, 'nombre accesible');
  const selection = await input.evaluate(el => ({ focused: document.activeElement === el, start: el.selectionStart, end: el.selectionEnd, length: el.value.length }));
  assert.equal(selection.focused, true, 'campo enfocado');
  assert.equal(selection.start, 0, 'selección desde el principio');
  assert.equal(selection.end, selection.length, 'selección completa');
  assert.equal(await page.locator('[role="status"]#article-share-status').textContent(), 'No se pudo copiar automáticamente. Selecciona el enlace para copiarlo');
  const dimensions = await page.evaluate(() => ({ scroll: document.documentElement.scrollWidth, viewport: document.documentElement.clientWidth }));
  assert.ok(dimensions.scroll <= dimensions.viewport + 1, `desbordamiento a 320px: ${dimensions.scroll}/${dimensions.viewport}`);
}

try {
  {
    const { page, context } = await openPage(() => {
      window.__mwCalls = { share: 0, copy: 0 };
      window.__deny = true;
      Object.defineProperty(navigator, 'share', { configurable: true, value: undefined });
      Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText: async value => {
        window.__mwCalls.copy++;
        window.__mwCalls.value = value;
        if (window.__deny) throw new DOMException('Denegado', 'NotAllowedError');
      } } });
    });
    try {
      const button = page.locator('[data-share-url]');
      const expected = await button.getAttribute('data-share-url');
      assert.ok(expected, 'URL declarada por el botón');
      const before = await page.locator('.article-utilities [data-share-url], .article-utilities [data-print]').evaluateAll(els => els.map(el => ({ x: el.getBoundingClientRect().x, y: el.getBoundingClientRect().y })));
      assert.equal(await page.locator('input.article-share-manual').count(), 0, 'sin campo en primera pintura');
      await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
      const stable = await page.locator('.article-utilities [data-share-url], .article-utilities [data-print]').evaluateAll(els => els.map(el => ({ x: el.getBoundingClientRect().x, y: el.getBoundingClientRect().y })));
      assert.deepEqual(stable, before, 'Compartir e Imprimir mantienen posición antes del clic');
      await page.evaluate(() => {
        window.__mwUnexpectedShifts = 0;
        new PerformanceObserver(list => {
          for (const entry of list.getEntries()) if (!entry.hadRecentInput) window.__mwUnexpectedShifts += entry.value;
        }).observe({ type: 'layout-shift' });
      });
      await button.click();
      await checkManual(page, expected);
      assert.deepEqual(await page.evaluate(() => window.__mwCalls), { share: 0, copy: 1, value: expected }, 'solo se intentó copiar');
      await button.click();
      await checkManual(page, expected);
      assert.equal(await page.evaluate(() => window.__mwCalls.copy), 2, 'segunda pulsación vuelve a intentar copiar sin duplicar');
      const updated = `${expected}?mw0020=retry`;
      await button.evaluate((el, value) => { el.dataset.shareUrl = value; }, updated);
      await button.click();
      await checkManual(page, updated);
      await page.waitForTimeout(150);
      assert.equal(await page.evaluate(() => window.__mwUnexpectedShifts), 0, 'ningún desplazamiento de layout sin interacción reciente');
      await page.evaluate(() => { window.__deny = false; });
      await button.click();
      await page.waitForFunction(() => document.querySelector('#article-share-status')?.textContent === 'Enlace copiado.');
      assert.equal(await page.locator('#article-share-status').textContent(), 'Enlace copiado.');
      assert.equal(await page.locator('input.article-share-manual').evaluate(el => el.hidden), true, 'copia correcta oculta la alternativa');
      assert.equal(await page.evaluate(() => window.__mwCalls.copy), 4);
      assert.equal(await page.evaluate(() => window.__mwCalls.value), updated);
      await page.evaluate(() => { window.__deny = true; });
      await button.click();
      await checkManual(page, updated);
      await page.evaluate(() => {
        Object.defineProperty(navigator, 'share', { configurable: true, value: async payload => {
          window.__mwCalls.share++;
          window.__mwShared = payload;
        } });
      });
      const copyBefore = await page.evaluate(() => window.__mwCalls.copy);
      await button.click();
      await page.waitForFunction(() => document.querySelector('#article-share-status')?.textContent === 'Compartido.');
      assert.equal(await page.locator('#article-share-status').textContent(), 'Compartido.');
      assert.equal(await page.locator('input.article-share-manual').evaluate(el => el.hidden), true, 'Web Share correcto oculta la alternativa');
      assert.equal(await page.evaluate(() => window.__mwCalls.share), 1);
      assert.equal(await page.evaluate(() => window.__mwCalls.copy), copyBefore, 'Web Share no debe usar portapapeles');
      assert.equal(await page.evaluate(() => window.__mwShared.url), updated);
    } finally { await context.close(); }
  }
  {
    const { page, context } = await openPage(() => {
      Object.defineProperty(navigator, 'share', { configurable: true, value: undefined });
      Object.defineProperty(navigator, 'clipboard', { configurable: true, value: undefined });
    });
    try {
      const expected = await page.locator('[data-share-url]').getAttribute('data-share-url');
      await page.locator('[data-share-url]').click();
      await checkManual(page, expected);
    } finally { await context.close(); }
  }
  {
    const { page, context } = await openPage(() => {
      window.__mwCalls = { share: 0, copy: 0 };
      Object.defineProperty(navigator, 'share', { configurable: true, value: async () => { window.__mwCalls.share++; } });
      Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText: async () => { window.__mwCalls.copy++; } } });
    });
    try {
      await page.locator('[data-share-url]').click();
      await page.waitForFunction(() => document.querySelector('#article-share-status')?.textContent === 'Compartido.');
      assert.equal(await page.locator('#article-share-status').textContent(), 'Compartido.');
      assert.equal(await page.locator('input.article-share-manual').count(), 0);
      assert.deepEqual(await page.evaluate(() => window.__mwCalls), { share: 1, copy: 0 });
    } finally { await context.close(); }
  }
  {
    const { page, context } = await openPage(() => {
      window.__mwCalls = { share: 0, copy: 0 };
      Object.defineProperty(navigator, 'share', { configurable: true, value: undefined });
      Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText: async () => { window.__mwCalls.copy++; } } });
    });
    try {
      await page.locator('[data-share-url]').click();
      await page.waitForFunction(() => document.querySelector('#article-share-status')?.textContent === 'Enlace copiado.');
      assert.equal(await page.locator('#article-share-status').textContent(), 'Enlace copiado.');
      assert.equal(await page.locator('input.article-share-manual').count(), 0);
      assert.deepEqual(await page.evaluate(() => window.__mwCalls), { share: 0, copy: 1 });
    } finally { await context.close(); }
  }
  {
    const { page, context } = await openPage(() => {
      window.__mwCalls = { share: 0, copy: 0 };
      Object.defineProperty(navigator, 'share', { configurable: true, value: async () => { window.__mwCalls.share++; throw new DOMException('Cancelado', 'AbortError'); } });
      Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText: async () => { window.__mwCalls.copy++; } } });
    });
    try {
      await page.locator('[data-share-url]').click();
      await page.waitForTimeout(50);
      assert.equal(await page.locator('#article-share-status').textContent(), '', 'AbortError no cambia el estado');
      assert.equal(await page.locator('input.article-share-manual').count(), 0, 'AbortError no crea campo');
      assert.deepEqual(await page.evaluate(() => window.__mwCalls), { share: 1, copy: 0 }, 'AbortError no intenta copiar');
    } finally { await context.close(); }
  }
  console.log('MW-0020 aceptación PASS');
} finally {
  await browser.close();
}
