import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || process.env.BASE_URL || 'http://127.0.0.1:8000';
const routes = ['/', '/autor.html', '/libros/', '/recomendaciones/', '/editoriales/', '/cuaderno/'];
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
const context = await browser.newContext({ serviceWorkers: 'block' });
try {
  await Promise.all(routes.flatMap(route => Array.from({ length: 2 }, async () => {
    const page = await context.newPage();
    const failures = [];
    page.on('response', response => {
      const url = new URL(response.url());
      if (url.origin === new URL(BASE).origin && url.pathname.endsWith('.css') && response.status() >= 400) failures.push(`${response.status()} ${url.pathname}`);
    });
    try {
      const response = await page.goto(new URL(route, BASE).href, { waitUntil: 'load', timeout: 30000 });
      assert.equal(response?.status(), 200, `${route}: respuesta HTML ${response?.status()}`);
      const result = await page.evaluate(() => {
        const heading = document.querySelector('h1');
        const body = getComputedStyle(document.body);
        const h = heading ? getComputedStyle(heading) : null;
        return { text: document.body.innerText.trim().length, family: body.fontFamily, size: parseFloat(body.fontSize), lineHeight: body.lineHeight, heading: heading?.innerText.trim(), headingSize: h ? parseFloat(h.fontSize) : 0 };
      });
      assert(result.text > 100, `${route}: documento vacío o incompleto (${result.text} caracteres)`);
      assert(result.family && result.family !== 'none', `${route}: familia tipográfica ausente`);
      assert(result.size >= 12, `${route}: cuerpo demasiado pequeño (${result.size}px)`);
      assert(result.heading && result.headingSize >= 12, `${route}: encabezado principal ausente o ilegible`);
      assert(result.lineHeight === 'normal' || parseFloat(result.lineHeight) > 0, `${route}: interlineado inválido (${result.lineHeight})`);
      assert.deepEqual(failures, [], `${route}: errores CSS ${failures.join(', ')}`);
    } finally {
      await page.close();
    }
  })));
  console.log('OK: 12 navegaciones concurrentes con tipografía y CSS verificables');
} finally {
  await browser.close();
}