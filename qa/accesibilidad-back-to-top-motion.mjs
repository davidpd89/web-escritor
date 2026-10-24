import assert from 'node:assert/strict';
import { check } from './accesibilidad-fixture.mjs';

for (const motion of ['reduce', 'no-preference']) {
  await check(async ({ page }) => {
    const button = page.locator('button.back-to-top');
    assert.equal(await button.count(), 1);
    assert.equal(await button.getAttribute('aria-label'), 'Volver al inicio de la página');
    const calls = await page.evaluate(() => {
      const history = [];
      window.scrollTo = options => history.push(options);
      document.querySelector('.back-to-top').click();
      return history;
    });
    assert.equal(calls.length, 1);
    assert.equal(calls[0].top, 0);
    assert.equal(calls[0].behavior, motion === 'reduce' ? 'auto' : 'smooth');
  }, { reducedMotion: motion });
}
console.log('accesibilidad-back-to-top-motion: PASS');
