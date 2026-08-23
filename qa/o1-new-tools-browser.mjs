// Verifica en un navegador real las dos herramientas nuevas de O.1
// (2026-08-23): Contador de palabras y Limpiador de manuscritos.
// Comprueba funcionamiento real, cero errores JS y que la CSP local-only
// no bloquea nada que la propia herramienta necesite.
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const MIME = new Map([
  ['.html', 'text/html; charset=utf-8'], ['.css', 'text/css; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'], ['.svg', 'image/svg+xml'], ['.woff2', 'font/woff2'],
]);
const server = createServer((req, res) => {
  const url = new URL(req.url, 'http://127.0.0.1');
  const clean = decodeURIComponent(url.pathname.split('?')[0]).replace(/^\/+/, '');
  const file = path.join(ROOT, clean.endsWith('/') || clean === '' ? clean + 'index.html' : clean);
  if (!fs.existsSync(file) || !fs.statSync(file).isFile()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': MIME.get(path.extname(file).toLowerCase()) || 'application/octet-stream' });
  res.end(fs.readFileSync(file));
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const ORIGIN = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

try {
  // 1) Contador de palabras
  {
    const context = await browser.newContext();
    const page = await context.newPage();
    const jsErrors = []; page.on('pageerror', (e) => jsErrors.push(String(e)));
    await page.goto(`${ORIGIN}/herramientas/contador-palabras/`, { waitUntil: 'load' });
    await page.fill('#wc-input', 'Hola mundo. Esta es una frase de prueba.');
    await page.waitForTimeout(100);
    assert(await page.locator('[data-wc-results]').isVisible(), 'contador: deben mostrarse resultados al escribir');
    const summaryText = await page.locator('[data-wc-summary]').textContent();
    assert.match(summaryText, /Palabras/, 'contador: debe mostrar el recuento de palabras');
    await page.click('[data-wc-sample]');
    await page.waitForTimeout(100);
    assert(await page.locator('[data-wc-results]').isVisible(), 'contador: el ejemplo debe producir resultados');
    await page.click('[data-wc-clear]');
    await page.waitForTimeout(100);
    assert(!(await page.locator('[data-wc-results]').isVisible()), 'contador: borrar debe ocultar resultados');
    assert.equal(jsErrors.length, 0, `contador: no debe haber excepciones JS: ${jsErrors.join(' | ')}`);
    await context.close();
  }

  // 2) Limpiador de manuscritos
  {
    const context = await browser.newContext();
    const page = await context.newPage();
    const jsErrors = []; page.on('pageerror', (e) => jsErrors.push(String(e)));
    await page.goto(`${ORIGIN}/herramientas/limpiador-manuscritos/`, { waitUntil: 'load' });

    const checkboxCount = await page.locator('[data-mc-rules] input[type=checkbox]').count();
    assert(checkboxCount >= 8, `limpiador: debe listar al menos 8 correcciones, encontradas ${checkboxCount}`);
    const allChecked = await page.locator('[data-mc-rules] input[type=checkbox]:checked').count();
    assert.equal(allChecked, checkboxCount, 'limpiador: todas las correcciones deben estar activas por defecto');

    await page.fill('#mc-input', 'Hola   mundo.   "Cita"  con  espacios.');
    await page.click('[data-mc-form] [type=submit]');
    await page.waitForTimeout(100);
    assert(await page.locator('[data-mc-results]').isVisible(), 'limpiador: deben mostrarse resultados');
    const cleaned = await page.locator('[data-mc-output]').inputValue();
    assert(!cleaned.includes('   '), 'limpiador: no deben quedar espacios múltiples en el resultado');
    assert(cleaned.includes('«Cita»'), `limpiador: las comillas rectas deben convertirse, obtenido: ${cleaned}`);

    // Desactivar una regla y volver a ejecutar: el resultado debe reflejarlo.
    await page.uncheck('[data-mc-rules] input[data-mc-rule="straightQuotes"]');
    await page.click('[data-mc-form] [type=submit]');
    await page.waitForTimeout(100);
    const cleanedNoQuotes = await page.locator('[data-mc-output]').inputValue();
    assert(cleanedNoQuotes.includes('"Cita"'), 'limpiador: con la regla desactivada las comillas rectas deben conservarse');

    assert.equal(jsErrors.length, 0, `limpiador: no debe haber excepciones JS: ${jsErrors.join(' | ')}`);
    await context.close();
  }

  console.log('o1-new-tools-browser: PASS');
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
