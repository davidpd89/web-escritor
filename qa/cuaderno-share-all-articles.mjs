import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const routes = fs.readdirSync('cuaderno', { withFileTypes: true }).filter(d => d.isDirectory() && d.name !== 'temas').map(d => `/cuaderno/${d.name}/`).filter(route => /"@type"\s*:\s*"Article"/.test(fs.readFileSync(`.${route}index.html`, 'utf8')));
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  assert.ok(routes.length >= 5);
  for (const route of routes) {
    const context = await browser.newContext();
    await context.route('**/*', r => new URL(r.request().url()).origin === BASE ? r.continue() : r.abort());
    await context.addInitScript(() => {
      Object.defineProperty(navigator, 'share', { configurable: true, value: undefined });
      Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText: async value => { window.__copied = value; } } });
      try { localStorage.setItem('nl-popup-ts', String(Date.now())); } catch {}
    });
    const page = await context.newPage();
    const response = await page.goto(BASE + route, { waitUntil: 'load' });
    assert.ok(response?.ok(), `${route}: carga fallida`);
    const canonical = await page.locator('link[rel="canonical"]').getAttribute('href');
    const button = page.locator('main [data-share-url]');
    assert.equal(await button.count(), 1, `${route}: botón Compartir ausente o duplicado`);
    assert.equal(await button.getAttribute('data-share-url'), canonical);
    await button.click();
    assert.equal(await page.evaluate(() => window.__copied), canonical, `${route}: portapapeles incorrecto`);
    assert.match(await page.locator('#article-share-status').innerText(), /Enlace copiado/i);
    await context.close();
  }
} finally { await browser.close(); }
console.log(`OK: compartir en ${routes.length} artículos`);
