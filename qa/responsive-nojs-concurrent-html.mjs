import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || process.env.SITE_BASE_URL || 'http://127.0.0.1:4173').replace(/\/$/, '');
const ROUTES = ['/accesibilidad/', '/editoriales/', '/herramientas/', '/mapa-del-sitio/', '/recomendaciones/'];
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

try {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const jobs = Array.from({ length: 4 }, () => ROUTES).flat();
  const results = await Promise.all(jobs.map(async (route, index) => {
    const page = await context.newPage();
    try {
      const response = await page.goto(`${ORIGIN}${route}`, { waitUntil: 'domcontentloaded', timeout: 20000 });
      const html = await page.content();
      const state = await page.evaluate(() => ({
        title: document.title.trim(),
        main: document.querySelector('main')?.textContent?.trim() || '',
        body: document.body?.textContent?.trim() || ''
      }));
      return { route, index, status: response?.status(), length: html.length, ...state };
    } finally {
      await page.close();
    }
  }));
  for (const r of results) {
    const label = `${r.route} petición ${r.index}`;
    assert.equal(r.status, 200, `${label}: HTTP ${r.status}`);
    assert.ok(r.length > 1000, `${label}: HTML vacío o incompleto (${r.length} caracteres)`);
    assert.ok(r.title, `${label}: título vacío`);
    assert.ok(r.main.length > 80, `${label}: contenido principal ausente (${r.main.length} caracteres)`);
    assert.ok(r.body.length >= r.main.length, `${label}: estructura del documento inconsistente`);
  }
  console.log(`PASS concurrent no-JS HTML: ${results.length} responses`);
  await context.close();
} finally {
  await browser.close();
}