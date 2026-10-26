import { chromium } from 'playwright';
import assert from 'node:assert/strict';

const BASE = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
const norm = s => s.replace(/\s+/g, ' ').trim();
try {
  for (const width of [320, 390, 768, 1440]) {
    const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    const response = await page.goto(BASE + '/recomendaciones/', { waitUntil: 'load' });
    assert(response?.ok(), `Catálogo @${width}: HTTP ${response?.status()}`);
    const books = await page.locator('[data-catalogue-book]').evaluateAll(cards => cards.map(card => ({
      title: card.querySelector('h3 a')?.textContent?.trim(),
      href: card.querySelector('h3 a')?.getAttribute('href')
    })));
    assert(books.length > 0, `Catálogo @${width}: ninguna tarjeta publicada`);
    for (const book of books) {
      assert(book.href?.startsWith('/recomendaciones/libros/'), `Catálogo @${width}: destino ausente para ${book.title}`);
      const result = await page.goto(BASE + book.href, { waitUntil: 'load' });
      assert(result?.ok(), `${book.href} @${width}: HTTP ${result?.status()}`);
      const actual = await page.locator('main h1').innerText();
      assert.equal(norm(actual), norm(book.title), `${book.href} @${width}: título de tarjeta ${book.title} distinto de H1 ${actual}`);
      const geometry = await page.locator('main h1').evaluate(el => {
        const r = el.getBoundingClientRect();
        return { left: r.left, right: r.right, viewport: innerWidth, scroll: document.documentElement.scrollWidth };
      });
      assert(geometry.left >= -1 && geometry.right <= geometry.viewport + 1, `${book.href} @${width}: H1 fuera del viewport: ${JSON.stringify(geometry)}`);
      assert(geometry.scroll <= width + 1, `${book.href} @${width}: desbordamiento horizontal ${geometry.scroll}`);
    }
    await context.close();
  }
  console.log('PASS: títulos de tarjetas y fichas, cuatro resoluciones');
} finally {
  await browser.close();
}
