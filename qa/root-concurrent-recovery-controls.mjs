import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const browser = await chromium.launch();
const ROUTES = ['/404.html', '/offline.html'];

try {
  const context = await browser.newContext({ reducedMotion: 'reduce', serviceWorkers: 'block' });
  await context.route('**/*', route => new URL(route.request().url()).origin === ORIGIN ? route.continue() : route.abort());
  await Promise.all(Array.from({ length: 8 }, async (_, index) => {
    const page = await context.newPage();
    const route = ROUTES[index % ROUTES.length];
    try {
      const response = await page.goto(ORIGIN + route, { waitUntil: 'load', timeout: 20000 });
      assert.ok(response?.ok(), `${route}: HTTP ${response?.status()}`);
      const controls = page.locator('main a[href], main button:not([disabled])');
      const count = await controls.count();
      assert.ok(count > 0, `${route}: no existen acciones de recuperación`);
      let accessible = 0;
      for (let i = 0; i < count; i++) {
        const control = controls.nth(i);
        if (!(await control.isVisible())) continue;
        const name = await control.evaluate(el => el.getAttribute('aria-label') || el.innerText || el.textContent || '');
        assert.ok(name.trim(), `${route}: control visible ${i} sin nombre accesible`);
        await control.focus();
        assert.equal(await control.evaluate(el => document.activeElement === el), true, `${route}: control ${i} no recibe foco`);
        accessible++;
      }
      assert.ok(accessible > 0, `${route}: ninguna acción visible y enfoc able`);
    } finally {
      await page.close();
    }
  }));
  await context.close();
} finally {
  await browser.close();
}
console.log('root-concurrent-recovery-controls: OK');