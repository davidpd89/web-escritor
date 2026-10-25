import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:8000';
const browser = await chromium.launch({ headless: true });

try {
  for (const route of ['/libros/', '/las-manecillas-del-recuerdo/']) {
    for (const width of [375, 1280]) {
      const page = await browser.newPage({ viewport: { width, height: 900 } });
      const response = await page.goto(new URL(route, origin).href);
      assert.ok(response?.ok(), `${route}: HTTP ${response?.status()}`);
      const selector = '.site-header a.header-buy';
      const link = page.locator(selector);
      await link.waitFor({ state: 'visible' });
      const normal = await link.evaluate(el => { const s = getComputedStyle(el); return { outline: s.outlineWidth, style: s.outlineStyle, shadow: s.boxShadow, border: s.borderColor, background: s.backgroundColor }; });
      await page.keyboard.press('Tab');
      await link.focus();
      const focused = await link.evaluate(el => { const s = getComputedStyle(el); return { outline: s.outlineWidth, style: s.outlineStyle, shadow: s.boxShadow, border: s.borderColor, background: s.backgroundColor, focusVisible: el.matches(':focus-visible') }; });
      assert.ok(focused.focusVisible, `${route} @${width}: enlace comercial sin :focus-visible`);
      const outline = focused.style !== 'none' && parseFloat(focused.outline) >= 1;
      const changed = focused.shadow !== normal.shadow || focused.border !== normal.border || focused.background !== normal.background;
      assert.ok(outline || changed, `${route} @${width}: sin indicador de foco; normal=${JSON.stringify(normal)}, foco=${JSON.stringify(focused)}`);
      await page.close();
    }
  }
} finally {
  await browser.close();
}
console.log('conversion-buy-keyboard-focus: OK');