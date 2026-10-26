import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';

const BASE = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const root = 'recomendaciones/libros';
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  const dirs = await fs.readdir(root, { withFileTypes: true });
  const routes = dirs.filter(d => d.isDirectory()).map(d => `/${root}/${d.name}/`).filter(route => true);
  assert(routes.length > 0, 'No se han descubierto fichas bibliográficas');
  let checked = 0;
  for (const route of routes) {
    if (!(await fs.stat(path.join(root, route.split('/').at(-2), 'index.html')).catch(() => null))) continue;
    const response = await page.goto(BASE + route, { waitUntil: 'load' });
    assert(response?.ok(), `${route}: HTTP ${response?.status()}`);
    const data = await page.evaluate(() => {
      const nodes = [...document.querySelectorAll('script[type="application/ld+json"]')].flatMap(s => {
        const obj = JSON.parse(s.textContent);
        return obj['@graph'] || [obj];
      });
      const book = nodes.find(n => n['@type'] === 'Book');
      const details = [...document.querySelectorAll('main details')];
      const edition = details.find(d => /Más datos de la edición/i.test(d.querySelector('summary')?.textContent || ''));
      const pairs = [...(edition?.querySelectorAll('dt') || [])].map(dt => ({ label: dt.textContent.trim(), value: dt.nextElementSibling?.textContent.trim() || '' }));
      return { isbn: String(book?.isbn || ''), visible: pairs.find(p => /^ISBN(?:-13)?$/i.test(p.label))?.value || '', title: document.querySelector('main h1')?.textContent.trim() };
    });
    if (!data.isbn) continue;
    checked++;
    assert.equal(data.visible.replace(/[\s-]/g, ''), data.isbn.replace(/[\s-]/g, ''), `${route} (${data.title}): ISBN visible ${data.visible} != JSON-LD ${data.isbn}`);
  }
  assert(checked > 0, 'No se ha comprobado ningún ISBN de una ficha real');
  console.log(`PASS: ${checked} fichas con ISBN visible y JSON-LD coherentes`);
} finally {
  await browser.close();
}
