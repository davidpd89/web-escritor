import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const ROUTE = '/donde-empieza-la-jaula/';
const browser = await chromium.launch({ headless: true });

try {
  for (const width of [320, 360, 390, 767, 768, 899, 900, 1199, 1200, 1440]) {
    const page = await browser.newPage({ viewport: { width, height: 900 } });
    const response = await page.goto(`${ORIGIN}${ROUTE}`, { waitUntil: 'networkidle' });
    assert.equal(response?.status(), 200, `${ROUTE} ${width}px: HTTP incorrecto`);
    await page.locator('.excerpt-field p').first().waitFor({ state: 'visible' });

    const result = await page.locator('.excerpt-field').evaluate(element => {
      const paragraphs = [...element.querySelectorAll('p')];
      const viewport = document.documentElement.clientWidth;
      const errors = [];
      for (const [index, paragraph] of paragraphs.entries()) {
        const rect = paragraph.getBoundingClientRect();
        const style = getComputedStyle(paragraph);
        const font = parseFloat(style.fontSize);
        const line = parseFloat(style.lineHeight);
        if (rect.width <= 0 || rect.height <= 0) errors.push(`p${index + 1}: caja vacía`);
        if (rect.left < -1 || rect.right > viewport + 1) errors.push(`p${index + 1}: límites ${rect.left}/${rect.right}, viewport ${viewport}`);
        if (!Number.isFinite(font) || !Number.isFinite(line) || font < 16 || line < font * 1.3) errors.push(`p${index + 1}: tipografía ${font}/${line}`);
      }
      return { count: paragraphs.length, errors, documentWidth: document.documentElement.scrollWidth, viewport };
    });

    assert.ok(result.count >= 20, `${ROUTE} ${width}px: capítulo incompleto, ${result.count} párrafos`);
    assert.deepEqual(result.errors, [], `${ROUTE} ${width}px: errores de lectura ${JSON.stringify(result.errors)}`);
    assert.ok(result.documentWidth <= result.viewport + 1, `${ROUTE} ${width}px: desbordamiento horizontal ${result.documentWidth} > ${result.viewport}`);
    await page.close();
  }
} finally {
  await browser.close();
}

console.log('OK: capítulo largo legible en todos los anchos');