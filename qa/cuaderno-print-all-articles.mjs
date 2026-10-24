import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const routes = fs.readdirSync('cuaderno', { withFileTypes: true }).filter(d => d.isDirectory() && d.name !== 'temas').map(d => `/cuaderno/${d.name}/`).filter(route => /"@type"\s*:\s*"Article"/.test(fs.readFileSync(`.${route}index.html`, 'utf8')));
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  for (const route of routes) {
    const context = await browser.newContext();
    await context.route('**/*', r => new URL(r.request().url()).origin === BASE ? r.continue() : r.abort());
    await context.addInitScript(() => { window.print = () => { window.__prints = (window.__prints || 0) + 1; }; });
    const page = await context.newPage();
    await page.goto(BASE + route, { waitUntil: 'load' });
    const button = page.locator('main [data-print]');
    assert.equal(await button.count(), 1, `${route}: botón Imprimir ausente`);
    await button.click();
    assert.equal(await page.evaluate(() => window.__prints), 1, `${route}: llamadas a print`);
    const canonical = await page.locator('link[rel="canonical"]').getAttribute('href');
    const source = page.locator('.article-print-source');
    assert.equal(await source.count(), 1, `${route}: falta procedencia`);
    assert.ok((await source.innerText()).includes(canonical), `${route}: procedencia incorrecta`);
    await page.emulateMedia({ media: 'print' });
    const state = await page.evaluate(() => Object.fromEntries(['.site-header', '.site-footer', '.article-toc', '.article-prose', '.article-print-source'].map(selector => {
      const el = document.querySelector(selector);
      return [selector, el ? getComputedStyle(el).display : 'absent'];
    })));
    assert.equal(state['.site-header'], 'none');
    assert.equal(state['.site-footer'], 'none');
    assert.notEqual(state['.article-prose'], 'none');
    assert.notEqual(state['.article-print-source'], 'none');
    if (state['.article-toc'] !== 'absent') assert.equal(state['.article-toc'], 'none');
    await context.close();
  }
} finally { await browser.close(); }
console.log(`OK: impresión de ${routes.length} artículos`);
