import assert from 'node:assert/strict';
import { withJaula } from './jaula-local-fixture.mjs';

for (const width of [320, 390, 768, 1200]) {
  await withJaula(async ({ page }) => {
    for (const factor of [1, 2, 4]) {
      await page.evaluate(value => { document.documentElement.style.fontSize = `${16 * value}px`; }, factor);
      const metrics = await page.locator('.excerpt-field').evaluate(el => {
        const style = getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        return { fontSize: parseFloat(style.fontSize), lineHeight: parseFloat(style.lineHeight), width: rect.width, left: rect.left, right: rect.right, overflow: document.documentElement.scrollWidth - innerWidth };
      });
      assert.ok(metrics.lineHeight / metrics.fontSize >= 1.45, `${width}/${factor}x: interlineado insuficiente`);
      assert.ok(metrics.width > 0, `${width}/${factor}x: columna colapsada`);
      assert.ok(metrics.overflow <= 1, `${width}/${factor}x: desplazamiento horizontal ${metrics.overflow}px`);
      assert.ok(metrics.left >= -1 && metrics.right <= width + 1, `${width}/${factor}x: texto fuera del viewport`);
    }
  }, { width });
}
console.log('jaula-reading-zoom-browser: OK');
