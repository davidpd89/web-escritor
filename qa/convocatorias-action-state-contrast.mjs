import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_ORIGIN || process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch();

try {
  const page = await browser.newPage();
  await page.goto(new URL('/convocatorias-escritores/', BASE).href);
  await page.locator('[data-radar-grid]').first().waitFor();

  const targets = [
    '[data-radar-source]',
    '[data-radar-calendar]',
    '.section-context__links a',
    '.tool-finder .text-action'
  ];

  const contrast = async locator => locator.evaluate(el => {
    const parse = value => (value.match(/[\d.]+/g) || []).slice(0, 3).map(Number);
    const lum = value => {
      const v = value.map(n => {
        n /= 255;
        return n <= 0.04045 ? n / 12.92 : ((n + 0.055) / 1.055) ** 2.4;
      });
      return v[0] * 0.2126 + v[1] * 0.7152 + v[2] * 0.0722;
    };
    let bg = [255, 255, 255];
    for (let node = el; node; node = node.parentElement) {
      const color = getComputedStyle(node).backgroundColor;
      if (color.startsWith('rgb(')) { bg = parse(color); break; }
    }
    const a = lum(parse(getComputedStyle(el).color));
    const b = lum(bg);
    return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
  });

  let checked = 0;
  for (const selector of targets) {
    const locator = page.locator(selector).filter({ visible: true }).first();
    if (!await locator.count()) continue;
    checked++;
    const label = `/convocatorias-escritores/: ${selector}`;
    assert.ok(await contrast(locator) >= 4.5, `${label}: contraste insuficiente en reposo`);
    await locator.hover();
    assert.ok(await contrast(locator) >= 4.5, `${label}: contraste insuficiente en hover`);
    await locator.focus();
    assert.ok(await contrast(locator) >= 4.5, `${label}: contraste insuficiente con foco`);
    const focus = await locator.evaluate(el => {
      const s = getComputedStyle(el);
      return { outline: s.outlineStyle, width: parseFloat(s.outlineWidth), shadow: s.boxShadow };
    });
    assert.ok((focus.outline !== 'none' && focus.width >= 2) || focus.shadow !== 'none', `${label}: foco sin indicador visual suficiente`);
  }
  assert.ok(checked >= 2, '/convocatorias-escritores/: no se encontraron suficientes acciones reales para comprobar');
} finally {
  await browser.close();
}