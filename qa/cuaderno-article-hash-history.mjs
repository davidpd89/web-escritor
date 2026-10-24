import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const routes = fs.readdirSync('cuaderno', { withFileTypes: true }).filter(d => d.isDirectory() && d.name !== 'temas').map(d => `/cuaderno/${d.name}/`).filter(route => fs.readFileSync(`.${route}index.html`, 'utf8').includes('data-article-toc'));
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  assert.ok(routes.length >= 2, 'No hay artículos con índice para comprobar');
  for (const route of routes) {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
    await context.route('**/*', r => new URL(r.request().url()).origin === BASE ? r.continue() : r.abort());
    const page = await context.newPage();
    await page.goto(BASE + route, { waitUntil: 'load' });
    const link = page.locator('[data-article-toc] a[href^="#"]').first();
    const hash = await link.getAttribute('href');
    assert.ok(hash?.length > 1);
    await link.click();
    assert.equal(new URL(page.url()).hash, hash, `${route}: hash tras clic`);
    await page.waitForTimeout(150);
    const top = await page.evaluate(id => {
      const target = document.getElementById(id);
      const header = document.querySelector('[data-header]');
      return { target: target?.getBoundingClientRect().top, header: header?.getBoundingClientRect().bottom || 0 };
    }, decodeURIComponent(hash.slice(1)));
    assert.ok(top.target !== undefined && top.target >= top.header - 2, `${route}: destino oculto por cabecera`);
    await page.goBack({ waitUntil: 'domcontentloaded' });
    assert.equal(new URL(page.url()).hash, '', `${route}: retroceso no elimina hash`);
    await page.goForward({ waitUntil: 'domcontentloaded' });
    assert.equal(new URL(page.url()).hash, hash, `${route}: avance no restaura hash`);
    await context.close();
  }
} finally { await browser.close(); }
console.log(`OK: navegación de fragmentos en ${routes.length} artículos`);
