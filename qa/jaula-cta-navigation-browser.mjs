import assert from 'node:assert/strict';
import { withJaula } from './jaula-local-fixture.mjs';

for (const width of [320, 389, 390, 620, 767, 768, 899, 900, 1199, 1200, 1440]) {
  await withJaula(async ({ page }) => {
    const cta = page.locator('.book-actions .primary-action');
    assert.equal(await cta.getAttribute('href'), '#capitulo-1');
    await cta.click();
    await page.waitForFunction(() => location.hash === '#capitulo-1');
    await page.waitForFunction(() => {
      const heading = document.querySelector('#jaula-capitulo-1');
      if (!heading) return false;
      const box = heading.getBoundingClientRect();
      return box.top >= 0 && box.top < innerHeight && box.width > 0;
    }, null, { timeout: 4000 });
    const state = await page.evaluate(() => ({ hash: location.hash, title: document.querySelector('#jaula-capitulo-1')?.textContent.trim(), overflow: document.documentElement.scrollWidth - innerWidth }));
    assert.equal(state.hash, '#capitulo-1');
    assert.equal(state.title, 'Capítulo 1');
    assert.ok(state.overflow <= 1, `${width}: desbordamiento de ${state.overflow}px`);
  }, { width, height: 844 });
}
console.log('jaula-cta-navigation-browser: OK');
