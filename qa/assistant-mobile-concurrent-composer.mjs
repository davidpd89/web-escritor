import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });

try {
  await Promise.all(Array.from({ length: 9 }, async (_, i) => {
    const width = [320, 360, 390][i % 3];
    const context = await browser.newContext({ viewport: { width, height: 780 } });
    try {
      const page = await context.newPage();
      const response = await page.goto(`${ORIGIN}/asistente/`, { waitUntil: 'domcontentloaded', timeout: 30000 });
      assert.ok(response?.ok(), `/asistente/ sesión ${i}: HTTP ${response?.status()}`);
      const field = page.locator('[data-assistant-query]');
      const send = page.locator('[data-assistant-submit]');
      await field.waitFor({ state: 'visible', timeout: 15000 });
      await field.fill('Libros del autor');
      assert.equal(await field.inputValue(), 'Libros del autor', `/asistente/ sesión ${i}: consulta alterada`);
      assert.ok(await send.isVisible(), `/asistente/ sesión ${i}: envío invisible`);
      const geometry = await send.evaluate(el => { const r = el.getBoundingClientRect(); return { left: r.left, right: r.right, width: r.width }; });
      assert.ok(geometry.width > 0 && geometry.left >= -2 && geometry.right <= width + 2, `/asistente/ ${width}px sesión ${i}: botón fuera de pantalla ${JSON.stringify(geometry)}`);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      assert.ok(overflow <= 2, `/asistente/ ${width}px sesión ${i}: overflow ${overflow}px`);
    } finally {
      await context.close();
    }
  }));
  console.log('PASS: formulario móvil del asistente');
} finally {
  await browser.close();
}