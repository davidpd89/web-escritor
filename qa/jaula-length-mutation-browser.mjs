import assert from 'node:assert/strict';
import { withJaula } from './jaula-local-fixture.mjs';

await withJaula(async ({ page }) => {
  await page.evaluate(() => {
    const longToken = 'Anticonstitucionalmente'.repeat(8);
    for (const selector of ['.book-lead', '.excerpt-field p:first-child', '.book-meta-ledger dd']) {
      const element = document.querySelector(selector);
      if (element) element.textContent += ` ${longToken} ${'texto adicional '.repeat(60)}`;
    }
  });
  for (const width of [320, 360, 389, 390, 620, 767, 768, 899, 900, 1200]) {
    await page.setViewportSize({ width, height: 844 });
    const layout = await page.evaluate(() => ({ overflow: document.documentElement.scrollWidth - innerWidth, regions: [...document.querySelectorAll('.book-lead, .excerpt-field, .book-meta-ledger')].map(el => { const r = el.getBoundingClientRect(); return { left: r.left, right: r.right, width: r.width }; }) }));
    assert.ok(layout.overflow <= 1, `${width}: overflow con contenido aumentado de ${layout.overflow}px`);
    for (const region of layout.regions) {
      assert.ok(region.left >= -1 && region.right <= width + 1, `${width}: región editorial fuera del viewport: ${JSON.stringify(region)}`);
      assert.ok(region.width > 0);
    }
  }
});
console.log('jaula-length-mutation-browser: OK');
