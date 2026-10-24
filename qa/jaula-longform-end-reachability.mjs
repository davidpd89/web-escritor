import assert from 'node:assert/strict';
import { withJaula } from './jaula-local-fixture.mjs';

for (const width of [320, 390, 768, 900, 1440]) {
  await withJaula(async ({ page }) => {
    const last = page.locator('.excerpt-field p').last();
    await last.scrollIntoViewIfNeeded();
    const result = await last.evaluate(el => {
      const r = el.getBoundingClientRect();
      const x = Math.max(1, Math.min(innerWidth - 2, r.left + r.width / 2));
      const y = Math.max(1, Math.min(innerHeight - 2, r.top + r.height / 2));
      return { text: el.textContent.trim(), visible: r.bottom > 0 && r.top < innerHeight, hit: el === document.elementFromPoint(x, y) || el.contains(document.elementFromPoint(x, y)) };
    });
    assert.ok(result.text.includes('volver a cerrarlo.'), `${width}: final alterado`);
    assert.ok(result.visible && result.hit, `${width}: final inaccesible visualmente`);
    await page.locator('.book-related').scrollIntoViewIfNeeded();
    assert.equal(await page.locator('.book-related .related-primary a').isVisible(), true);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
    assert.ok(overflow <= 1, `${width}: overflow ${overflow}`);
  }, { width });
}
console.log('jaula-longform-end-reachability: OK');
