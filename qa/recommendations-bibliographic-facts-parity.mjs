import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

const BASE = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const dirs = (await fs.readdir('recomendaciones/libros', { withFileTypes: true })).filter(d => d.isDirectory());
const browser = await chromium.launch({ headless: true });
const months = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
function civilDate(text) {
  const m = text.toLocaleLowerCase('es').match(/(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})/);
  if (!m) return null;
  const month = months.indexOf(m[2]);
  return month < 0 ? null : `${m[3]}-${String(month + 1).padStart(2, '0')}-${m[1].padStart(2, '0')}`;
}
try {
  const page = await browser.newPage();
  let checked = 0;
  for (const dir of dirs) {
    const route = `/recomendaciones/libros/${dir.name}/`;
    if (!(await fs.stat(`recomendaciones/libros/${dir.name}/index.html`).catch(() => null))) continue;
    const response = await page.goto(BASE + route, { waitUntil: 'load' });
    assert(response?.ok(), `${route}: HTTP ${response?.status()}`);
    const facts = await page.evaluate(() => {
      const nodes = [...document.querySelectorAll('script[type="application/ld+json"]')].flatMap(s => { const o = JSON.parse(s.textContent); return o['@graph'] || [o]; });
      const book = nodes.find(n => n['@type'] === 'Book');
      const visible = [...document.querySelectorAll('.catalogue-facts dt')].map(dt => [dt.textContent.trim(), dt.nextElementSibling?.textContent.trim() || '']);
      return { book, visible: Object.fromEntries(visible), title: document.querySelector('main h1')?.textContent.trim() };
    });
    if (!facts.book) continue;
    checked++;
    if (facts.book.numberOfPages != null) {
      const rendered = Number((facts.visible['Páginas'] || '').replace(/\D/g, ''));
      assert.equal(rendered, Number(facts.book.numberOfPages), `${route} (${facts.title}): páginas visibles ${rendered} != JSON-LD ${facts.book.numberOfPages}`);
    }
    if (facts.book.datePublished) {
      const rendered = civilDate(facts.visible['Publicación'] || '');
      assert.equal(rendered, facts.book.datePublished.slice(0, 10), `${route} (${facts.title}): fecha visible ${facts.visible['Publicación']} != JSON-LD ${facts.book.datePublished}`);
    }
  }
  assert(checked > 0, 'No se han comprobado fichas con Book JSON-LD');
  console.log(`PASS: ${checked} fichas, fechas y páginas bibliográficas`);
} finally {
  await browser.close();
}
