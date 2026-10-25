import { chromium } from 'playwright';
import assert from 'node:assert/strict';

const base = (process.env.BASE_URL || process.env.SITE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const browser = await chromium.launch({ headless: true });
try {
  for (const width of [320, 360, 390]) {
    const page = await browser.newPage({ viewport: { width, height: 780 } });
    try {
      await page.goto(`${base}/redes-sociales/`, { waitUntil: 'domcontentloaded' });
      const trigger = page.locator('[data-explore-open]');
      const dialog = page.locator('[data-explore-dialog]');
      await trigger.waitFor({ state: 'visible' });
      assert.ok(await trigger.isEnabled(), `redes-sociales ${width}px: menú deshabilitado`);
      await trigger.click();
      await dialog.waitFor({ state: 'visible' });
      assert.ok(await dialog.evaluate(el => el.open), `redes-sociales ${width}px: diálogo no abierto`);
      const close = dialog.locator('[data-explore-close]');
      await close.waitFor({ state: 'visible' });
      await close.click();
      await dialog.waitFor({ state: 'hidden' });
      assert.equal(await dialog.evaluate(el => el.open), false, `redes-sociales ${width}px: diálogo sigue abierto`);
      assert.ok(await trigger.isVisible(), `redes-sociales ${width}px: botón de menú perdido`);
    } finally {
      await page.close();
    }
  }
} finally {
  await browser.close();
}
