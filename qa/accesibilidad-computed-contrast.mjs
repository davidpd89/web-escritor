import assert from 'node:assert/strict';
import { check } from './accesibilidad-fixture.mjs';

await check(async ({ page }) => {
  const results = await page.evaluate(() => {
    const rgb = value => (value.match(/[\d.]+/g) || []).slice(0, 3).map(Number);
    const luminance = values => values.map(v => { const x = v / 255; return x <= .04045 ? x / 12.92 : ((x + .055) / 1.055) ** 2.4; }).reduce((sum, x, i) => sum + x * [.2126, .7152, .0722][i], 0);
    const contrast = (a, b) => { const x = luminance(a); const y = luminance(b); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05); };
    return ['.cuaderno-masthead h1', '.v1-section .eyebrow', '.v1-section a[href]'].map(selector => {
      const el = document.querySelector('main ' + selector);
      if (!el) return { selector, missing: true };
      const css = getComputedStyle(el);
      let node = el;
      let background = [255, 255, 255];
      while (node) {
        const value = getComputedStyle(node).backgroundColor;
        if (value && value !== 'transparent' && !value.endsWith(', 0)')) { background = rgb(value); break; }
        node = node.parentElement;
      }
      const size = parseFloat(css.fontSize);
      const large = size >= 24 || (size >= 18.66 && Number(css.fontWeight) >= 700);
      return { selector, ratio: contrast(rgb(css.color), background), required: large ? 3 : 4.5 };
    });
  });
  for (const result of results) {
    assert.equal(result.missing, undefined, `Control ausente: ${result.selector}`);
    assert.ok(result.ratio >= result.required, `${result.selector}: contraste ${result.ratio.toFixed(2)}:1, mínimo ${result.required}:1`);
  }
});
console.log('accesibilidad-computed-contrast: PASS');
