import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const browser = await chromium.launch();

try {
  const context = await browser.newContext({ reducedMotion: 'reduce', serviceWorkers: 'block' });
  await context.route('**/*', route => new URL(route.request().url()).origin === ORIGIN ? route.continue() : route.abort());
  const results = await Promise.all(Array.from({ length: 8 }, async (_, index) => {
    const page = await context.newPage();
    try {
      const response = await page.goto(ORIGIN + '/offline.html', { waitUntil: 'load', timeout: 20000 });
      assert.ok(response?.ok(), `offline.html sesión ${index}: HTTP ${response?.status()}`);
      const buttons = page.locator('main button:visible:not([disabled])');
      const count = await buttons.count();
      assert.ok(count > 0, `offline.html sesión ${index}: faltan botones visibles`);
      const names = [];
      for (let i = 0; i < count; i++) {
        const button = buttons.nth(i);
        await button.focus();
        const state = await button.evaluate(el => ({ focused: document.activeElement === el, name: el.getAttribute('aria-label') || el.textContent.trim(), visible: !!el.getClientRects().length }));
        assert.ok(state.focused && state.visible && state.name, `offline.html sesión ${index}: botón ${i} sin foco, nombre o visibilidad`);
        names.push(state.name);
      }
      return names;
    } finally {
      await page.close();
    }
  }));
  for (let i = 1; i < results.length; i++) {
    assert.deepEqual(results[i], results[0], `offline.html sesión ${i}: secuencia de controles distinta de la sesión 0`);
  }
  await context.close();
} finally {
  await browser.close();
}
console.log('root-concurrent-keyboard-order: OK');