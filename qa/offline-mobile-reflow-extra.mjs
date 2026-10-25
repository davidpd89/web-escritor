import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const html = readFileSync(resolve('offline.html'), 'utf8');
const browser = await chromium.launch({ headless: true });
try {
  for (const width of [320, 360, 390]) {
    const page = await browser.newPage({ viewport: { width, height: 720 }, reducedMotion: 'reduce' });
    await page.route('**/*', route => route.abort());
    await page.setContent(html, { waitUntil: 'domcontentloaded' });
    const state = await page.evaluate(() => ({
      width: innerWidth,
      scroll: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth),
      controls: [...document.querySelectorAll('[data-retry], [data-back]')].filter(e => getComputedStyle(e).display !== 'none').map(e => {
        const r = e.getBoundingClientRect();
        return { left: r.left, right: r.right, height: r.height };
      })
    }));
    assert.ok(state.scroll <= state.width + 1, `Overflow at ${width}: ${state.scroll}`);
    assert.ok(state.controls.length >= 1, `No recovery control at ${width}`);
    for (const c of state.controls) {
      assert.ok(c.left >= -1 && c.right <= width + 1, `Control outside viewport at ${width}`);
      assert.ok(c.height >= 44, `Control touch target too small at ${width}`);
    }
    await page.close();
  }
} finally {
  await browser.close();
}
console.log('offline-mobile-reflow-extra: OK');