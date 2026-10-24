import assert from 'node:assert/strict';
import { check } from './accesibilidad-fixture.mjs';

await check(async ({ page }) => {
  await page.route('**/*.woff2*', route => route.abort());
  for (const width of [320, 390]) {
    await page.setViewportSize({ width, height: 850 });
    await page.reload({ waitUntil: 'load' });
    await page.addStyleTag({ content: 'html { font-size: 200% !important; }' });
    const result = await page.evaluate(() => {
      const main = document.querySelector('main');
      const headings = [...main.querySelectorAll('h1,h2')];
      return { overflow: document.documentElement.scrollWidth > innerWidth + 1, headings: headings.length, readable: headings.every(el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== 'hidden'; }), contact: Boolean(main.querySelector('a[data-email-reveal]')) };
    });
    assert.equal(result.overflow, false, `${width}: overflow con zoom`);
    assert.ok(result.headings >= 6);
    assert.equal(result.readable, true);
    assert.equal(result.contact, true);
  }
});
console.log('accesibilidad-font-failure-zoom: PASS');
