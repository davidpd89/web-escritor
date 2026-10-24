import assert from 'node:assert/strict';
import { check } from './accesibilidad-fixture.mjs';

await check(async ({ page }) => {
  const selectors = ['.editorial-breadcrumb a', 'main [data-email-reveal]', '.site-footer nav[aria-label="Legal"] a[href="/privacidad.html"]'];
  for (const width of [320, 390, 768, 1280]) {
    await page.setViewportSize({ width, height: 850 });
    for (const selector of selectors) {
      const link = page.locator(selector).first();
      assert.equal(await link.count(), 1, selector);
      await link.scrollIntoViewIfNeeded();
      const result = await link.evaluate(el => {
        const r = el.getClientRects()[0];
        if (!r) return { hit: false, width: 0 };
        const x = Math.max(0, Math.min(innerWidth - 1, (r.left + r.right) / 2));
        const y = Math.max(0, Math.min(innerHeight - 1, (r.top + r.bottom) / 2));
        const top = document.elementFromPoint(x, y);
        return { hit: Boolean(top && (top === el || el.contains(top))), width: r.width };
      });
      assert.ok(result.width > 0, `${width}: enlace sin superficie ${selector}`);
      assert.ok(result.hit, `${width}: enlace cubierto ${selector}`);
    }
  }
});
console.log('accesibilidad-hit-testing: PASS');
