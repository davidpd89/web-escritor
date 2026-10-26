import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

const BASE = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const dirs = (await fs.readdir('recomendaciones/libros', { withFileTypes: true })).filter(d => d.isDirectory());
const browser = await chromium.launch({ headless: true });
try {
  let checked = 0;
  for (const width of [320, 390, 768, 1440]) {
    const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    for (const dir of dirs) {
      const route = `/recomendaciones/libros/${dir.name}/`;
      if (!(await fs.stat(`recomendaciones/libros/${dir.name}/index.html`).catch(() => null))) continue;
      const response = await page.goto(BASE + route, { waitUntil: 'load' });
      assert(response?.ok(), `${route} @${width}: HTTP ${response?.status()}`);
      await page.evaluate(() => document.fonts.ready);
      const prices = await page.locator('.catalogue-facts .catalogue-pvp').evaluateAll(nodes => nodes.map(el => {
        const rect = el.getBoundingClientRect();
        const style = getComputedStyle(el);
        const range = document.createRange();
        range.selectNodeContents(el);
        const textRects = [...range.getClientRects()].map(r => ({ left: r.left, right: r.right, width: r.width }));
        return { text: el.textContent.trim(), rect: { left: rect.left, right: rect.right, width: rect.width }, textRects, display: style.display, visibility: style.visibility, opacity: Number(style.opacity), viewport: innerWidth };
      }));
      for (const price of prices) {
        checked++;
        assert.match(price.text, /\d+(?:[.,]\d{1,2})?\s*€/u, `${route} @${width}: PVP sin cantidad monetaria válida: ${price.text}`);
        assert(price.display !== 'none' && price.visibility === 'visible' && price.opacity > 0, `${route} @${width}: PVP oculto: ${price.text}`);
        assert(price.rect.width > 0 && price.rect.left >= -1 && price.rect.right <= width + 1, `${route} @${width}: caja PVP fuera del viewport: ${JSON.stringify(price)}`);
        assert(price.textRects.length > 0 && price.textRects.every(r => r.width > 0 && r.left >= -1 && r.right <= width + 1), `${route} @${width}: texto PVP desbordado: ${JSON.stringify(price)}`);
      }
    }
    await context.close();
  }
  assert(checked > 0, 'No se ha comprobado ningún PVP publicado');
  console.log(`PASS: ${checked} observaciones de PVP en cuatro resoluciones`);
} finally {
  await browser.close();
}
