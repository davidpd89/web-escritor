import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';

const base = (process.env.SITE_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const data = JSON.parse(fs.readFileSync('data/reading-catalogue.json', 'utf8'));
const books = data.libros.filter(b => b.estado === 'publicado');
assert.ok(books.length, 'No hay fichas publicadas para comprobar');
const browser = await chromium.launch({headless:true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});
try {
  for (const width of [320,768,1024,1440]) {
    const page = await browser.newPage({viewport:{width,height:900}});
    for (const book of books) {
      const route = `/recomendaciones/libros/${book.slug}/`;
      const response = await page.goto(base + route, {waitUntil:'domcontentloaded'});
      assert.equal(response.status(),200,`${route} ${width}px: HTTP inesperado`);
      await page.locator('.catalogue-book-layout').waitFor({state:'visible'});
      await page.evaluate(() => document.fonts.ready);
      const result = await page.evaluate(() => {
        const selectors = ['.catalogue-book-layout','.catalogue-book-heading','.catalogue-cover-panel'];
        return {
          scroll:document.documentElement.scrollWidth,
          viewport:document.documentElement.clientWidth,
          boxes:selectors.flatMap(s => [...document.querySelectorAll(s)].filter(e => e.getClientRects().length).map(e => ({selector:s,left:e.getBoundingClientRect().left,right:e.getBoundingClientRect().right})))
        };
      });
      assert.ok(result.boxes.length >= 2,`${route} ${width}px: estructura de ficha incompleta`);
      assert.ok(result.scroll <= result.viewport + 2,`${route} ${width}px: documento ${result.scroll}px > ventana ${result.viewport}px`);
      for (const box of result.boxes) {
        assert.ok(box.left >= -2 && box.right <= width + 2,`${route} ${width}px: ${box.selector} ocupa ${box.left.toFixed(1)}..${box.right.toFixed(1)}px`);
      }
    }
    await page.close();
  }
} finally { await browser.close(); }
console.log(`PASS: geometría de ${books.length} fichas en cuatro resoluciones`);
