import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const route = '/convocatorias-escritores/';
const browser = await chromium.launch();
try {
  for (const width of [320, 390, 1440]) {
    const context = await browser.newContext({ viewport: { width, height: 900 } });
    const page = await context.newPage();
    try {
      const response = await page.goto(origin + route, { waitUntil: 'load' });
      assert.equal(response?.status(), 200, `${route} ${width}px: HTTP incorrecto`);
      await page.waitForFunction(() => Boolean(window.DPRadarDates));
      for (const selector of ['[data-radar-search]', '[data-radar-type]', '[data-radar-genre]', 'select#radar-kind[data-radar-kind]', '[data-radar-soon]', '[data-radar-expired]']) {
        const result = await page.locator(selector).evaluate(el => {
          const labels = el.labels ? [...el.labels].map(label => label.textContent.trim()).join(' ') : '';
          const named = el.getAttribute('aria-label') || labels || (el.getAttribute('aria-labelledby') || '').split(/\s+/).map(id => document.getElementById(id)?.textContent?.trim() || '').join(' ');
          return { named: named.trim(), disabled: el.disabled };
        });
        assert.ok(result.named, `${route} ${width}px: ${selector} sin nombre accesible`);
        assert.equal(result.disabled, false, `${route} ${width}px: ${selector} deshabilitado`);
      }
      const cases = [
        ['inicial', async () => {}],
        ['busqueda', async () => page.locator('[data-radar-search]').fill('alfaguara')],
        ['sin-resultados', async () => page.locator('[data-radar-search]').fill('zzzz-sin-resultados')],
        ['limpiar', async () => page.locator('[data-radar-clear]').click()],
        ['vencidas', async () => page.locator('[data-radar-expired]').check()]
      ];
      for (const [name, action] of cases) {
        await action();
        await page.waitForFunction(() => {
          const visible = [...document.querySelectorAll('[data-radar-item]')].filter(el => !el.hidden && !el.closest('[hidden]')).length;
          return document.querySelector('[data-radar-count]')?.textContent?.startsWith(`${visible} `);
        });
        const result = await page.evaluate(() => {
          const node = document.querySelector('[data-radar-count]');
          const visible = [...document.querySelectorAll('[data-radar-item]')].filter(el => !el.hidden && !el.closest('[hidden]')).length;
          return { visible, text: node?.textContent?.trim(), role: node?.getAttribute('role'), live: node?.getAttribute('aria-live'), hidden: node?.hidden || Boolean(node?.closest('[hidden]')) };
        });
        assert.equal(result.hidden, false, `${route} ${width}px ${name}: contador oculto`);
        assert.ok(result.role === 'status' || ['polite', 'assertive'].includes(result.live), `${route} ${width}px ${name}: contador sin región anunciable`);
        assert.ok(result.text.startsWith(`${result.visible} `), `${route} ${width}px ${name}: contador ${result.text}, visibles ${result.visible}`);
        if (name === 'sin-resultados') {
          assert.equal(result.visible, 0, `${route} ${width}px: búsqueda sin resultados no vacía`);
          assert.equal(await page.locator('[data-radar-filter-empty]').isVisible(), true, `${route} ${width}px: falta mensaje de vacío`);
        }
      }
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}