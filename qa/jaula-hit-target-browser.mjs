import assert from 'node:assert/strict';
import { withJaula } from './jaula-local-fixture.mjs';

for (const width of [320, 390, 768, 900, 1440]) {
  await withJaula(async ({ page }) => {
    for (const selector of ['.book-actions .primary-action', '.book-actions .text-action', '.header-home', '.explore-trigger', '.book-related .related-primary a']) {
      const target = page.locator(selector);
      await target.scrollIntoViewIfNeeded();
      const hit = await target.evaluate(el => {
        const r = el.getBoundingClientRect();
        const x = r.left + r.width / 2;
        const y = r.top + r.height / 2;
        const found = document.elementFromPoint(x, y);
        return { width: r.width, height: r.height, visible: getComputedStyle(el).visibility === 'visible', reachesTarget: found === el || el.contains(found), interceptedBy: found?.tagName || null };
      });
      assert.ok(hit.visible && hit.width > 0 && hit.height > 0, `${width}: ${selector} no tiene caja visible`);
      assert.ok(hit.reachesTarget, `${width}: ${selector} interceptado por ${hit.interceptedBy}`);
    }
  }, { width });
}
console.log('jaula-hit-target-browser: OK');
