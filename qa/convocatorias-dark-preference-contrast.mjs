import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_ORIGIN || process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch();

try {
  const selectors = ['.tool-hero h1', '.tool-hero__lead', '.radar-card h2', '.radar-org', '.tool-input', '.tool-select', '.radar-badge'];
  const results = {};

  for (const scheme of ['light', 'dark']) {
    const context = await browser.newContext({ colorScheme: scheme });
    const page = await context.newPage();
    await page.goto(new URL('/convocatorias-escritores/', BASE).href);
    await page.locator('[data-radar-grid]').first().waitFor();
    results[scheme] = await page.evaluate(selectors => {
      const rgb = value => (value.match(/[\d.]+/g) || []).slice(0, 3).map(Number);
      const luminance = color => {
        const v = color.map(x => {
          x /= 255;
          return x <= 0.04045 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4;
        });
        return v[0] * 0.2126 + v[1] * 0.7152 + v[2] * 0.0722;
      };
      return selectors.flatMap(selector => {
        const el = [...document.querySelectorAll(selector)].find(node => node.getClientRects().length);
        if (!el) return [];
        const fg = rgb(getComputedStyle(el).color);
        let bg = [255, 255, 255];
        for (let node = el; node; node = node.parentElement) {
          const value = getComputedStyle(node).backgroundColor;
          if (value.startsWith('rgb(')) { bg = rgb(value); break; }
        }
        const a = luminance(fg);
        const b = luminance(bg);
        return [{ selector, ratio: (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05) }];
      });
    }, selectors);
    assert.ok(results[scheme].length >= 5, `/convocatorias-escritores/: ${scheme} sin muestras cromáticas suficientes`);
    for (const item of results[scheme]) {
      assert.ok(item.ratio >= 4.5, `/convocatorias-escritores/: ${scheme}, ${item.selector}, contraste ${item.ratio.toFixed(2)}:1`);
    }
    await context.close();
  }
  assert.deepEqual(results.light.map(x => x.selector), results.dark.map(x => x.selector), '/convocatorias-escritores/: cambió la cobertura visible entre esquemas');
} finally {
  await browser.close();
}