// Verifica en un navegador real ambos formatos de Distribucion de POV
// (O.2, 2026-08-23): el formato de escenas existente sigue funcionando
// igual, y el nuevo formato explicito "POV | palabras" (modo Totales)
// produce el resultado correcto sin reinterpretar el formato de escenas.
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
  const context = await browser.newContext();
  const page = await context.newPage();
  const jsErrors = [];
  page.on('pageerror', (e) => jsErrors.push(String(e)));
  await page.goto(`${ORIGIN}/herramientas/distribucion-pov/`, { waitUntil: 'load' });

  // 1) Modo por defecto (escenas): el flujo existente sigue funcionando.
  await page.click('[data-pov-sample]');
  await page.click('[data-pov-run]');
  await page.waitForTimeout(150);
  assert(await page.locator('[data-pov-results]').isVisible(), 'modo escenas: deben mostrarse resultados');
  assert(await page.locator('[data-pov-sequence-block]').isVisible(), 'modo escenas: la secuencia debe ser visible');
  const scenesHeadText = await page.locator('[data-pov-summary-head]').textContent();
  assert.match(scenesHeadText, /Racha/, 'modo escenas: la cabecera debe incluir Racha máx.');

  // 2) Cambiar al modo Totales explícito: NO reinterpreta el formato de
  //    escenas, usa su propio campo y su propio parser.
  await page.selectOption('#pov-format-mode', 'totals');
  await page.click('[data-pov-sample]');
  const totalsValue = await page.locator('#pov-input-totals').inputValue();
  assert.match(totalsValue, /Ana \| 24500/, 'modo totales: el ejemplo debe rellenar el campo de totales, no el de escenas');
  await page.click('[data-pov-run]');
  await page.waitForTimeout(150);
  assert(await page.locator('[data-pov-results]').isVisible(), 'modo totales: deben mostrarse resultados');
  assert(!(await page.locator('[data-pov-sequence-block]').isVisible()), 'modo totales: la secuencia no aplica (no hay orden de escenas) y debe ocultarse');
  const totalsHeadText = await page.locator('[data-pov-summary-head]').textContent();
  assert.doesNotMatch(totalsHeadText, /Racha/, 'modo totales: la cabecera NO debe prometer Racha máx. (no existe en este formato)');
  const summaryRows = await page.locator('[data-pov-summary] tr').count();
  assert.equal(summaryRows, 3, 'modo totales: debe haber una fila por POV (Ana, Bruno, Clara)');

  // 3) Formato incorrecto en modo totales produce un error claro, no un
  //    resultado silenciosamente reinterpretado.
  await page.fill('#pov-input-totals', 'Ana | Bruno');
  await page.click('[data-pov-run]');
  await page.waitForTimeout(150);
  const statusText = await page.locator('[data-pov-status]').textContent();
  assert.match(statusText, /enteros? positivos?/i, 'debe explicar por qué falla (palabras no numéricas), no fallar en silencio ni reinterpretar');

  assert.equal(jsErrors.length, 0, `no debe haber excepciones JS: ${jsErrors.join(' | ')}`);
  await context.close();
  console.log('pov-distribucion-format-browser: PASS');
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
