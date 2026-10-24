import assert from 'node:assert/strict';
import { check } from './accesibilidad-fixture.mjs';

await check(async ({ page }) => {
  const opener = page.locator('[data-explore-open]').first();
  await opener.click();
  const toggle = page.locator('.explore-row__toggle').first();
  await toggle.click();
  const dialog = page.locator('[data-explore-dialog]');
  for (const [width, height] of [[320, 568], [667, 375], [390, 500], [768, 1024], [1280, 800], [320, 568]]) {
    await page.setViewportSize({ width, height });
    assert.equal(await dialog.evaluate(el => el.open), true);
    assert.equal(await toggle.getAttribute('aria-expanded'), 'true');
    const state = await page.evaluate(() => {
      const close = document.querySelector('[data-explore-close]');
      const rect = close.getBoundingClientRect();
      return { overflow: document.documentElement.scrollWidth > innerWidth + 1, visible: rect.width > 0 && rect.height > 0 && rect.right > 0 && rect.left < innerWidth && rect.bottom > 0 && rect.top < innerHeight };
    });
    assert.equal(state.overflow, false, `${width}x${height}`);
    assert.equal(state.visible, true, `Cerrar no disponible en ${width}x${height}`);
  }
  await page.locator('[data-explore-close]').click();
  await page.waitForFunction(() => !document.querySelector('[data-explore-dialog]').open);
  await page.waitForFunction(() => document.activeElement?.matches('[data-explore-open]'));
});
console.log('accesibilidad-responsive-state: PASS');
