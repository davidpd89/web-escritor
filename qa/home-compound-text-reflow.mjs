import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { localPage, readyHome } from './home-family-local-fixture.mjs';

const browser = await chromium.launch({ headless: true });
try {
  for (const width of [320, 390, 768]) {
    const { context, page } = await localPage(browser, {
      viewport: { width, height: 780 }
    });
    await readyHome(page);

    for (const scale of [1, 1.5, 2]) {
      await page.evaluate(scale => {
        document.documentElement.style.fontSize = `${scale * 100}%`;
      }, scale);

      await page.locator('#faq > summary').click();
      const state = await page.evaluate(() => ({
        width: document.documentElement.clientWidth,
        scroll: document.documentElement.scrollWidth,
        faqVisible: getComputedStyle(document.querySelector('#faq')).visibility,
        buttons: [...document.querySelectorAll('.editorial-home-flow button')]
          .filter(el => getComputedStyle(el).display !== 'none')
          .map(el => ({ width: el.getBoundingClientRect().width, height: el.getBoundingClientRect().height }))
      }));

      assert(state.scroll <= state.width + 1,
        `overflow ancho=${width} escala=${scale}: ${state.scroll}/${state.width}`);
      assert.equal(state.faqVisible, 'visible');
      assert(state.buttons.every(b => b.width >= 24 && b.height >= 24));
      await page.locator('#faq > summary').click();
    }
    await context.close();
  }
  console.log('PASS home-compound-text-reflow');
} finally {
  await browser.close();
}