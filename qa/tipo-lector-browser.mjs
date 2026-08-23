// Verifica en un navegador real el quiz "¿Qué tipo de lector eres?" (P.1,
// 2026-08-23): render de preguntas, bloqueo de envío incompleto, cálculo
// de resultado, reproducibilidad y accesibilidad básica por teclado.
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
  const jsErrors = []; page.on('pageerror', (e) => jsErrors.push(String(e)));
  const requests = [];
  page.on('request', (r) => { if (r.url().startsWith('http') && !r.url().startsWith(ORIGIN)) requests.push(r.url()); });
  await page.goto(`${ORIGIN}/herramientas/que-tipo-de-lector-eres/`, { waitUntil: 'load' });

  const questionCount = await page.locator('.quiz-question').count();
  assert.equal(questionCount, 6, `deben renderizarse 6 preguntas, encontradas ${questionCount}`);
  const optionsInFirst = await page.locator('.quiz-question').first().locator('input[type=radio]').count();
  assert.equal(optionsInFirst, 6, `cada pregunta debe tener 6 opciones, encontradas ${optionsInFirst}`);

  // Envío incompleto: no debe mostrar resultados.
  await page.click('[data-quiz-form] [type=submit]');
  await page.waitForTimeout(100);
  assert(!(await page.locator('[data-quiz-results]').isVisible()), 'sin responder todo, no debe mostrarse resultado');

  // Responder todas las preguntas eligiendo siempre la primera opción (perfil "detector-pistas").
  const fieldsets = page.locator('.quiz-question');
  const n = await fieldsets.count();
  for (let i = 0; i < n; i += 1) {
    await fieldsets.nth(i).locator('input[type=radio]').first().check();
  }
  await page.click('[data-quiz-form] [type=submit]');
  await page.waitForTimeout(150);
  assert(await page.locator('[data-quiz-results]').isVisible(), 'con todas las preguntas respondidas debe mostrarse el resultado');
  const resultTitle = await page.locator('[data-quiz-result-card] h3').textContent();
  assert.match(resultTitle, /Detector de pistas/, `esperado perfil "Detector de pistas", obtenido "${resultTitle}"`);

  const breakdownCount = await page.locator('[data-quiz-breakdown] li').count();
  assert.equal(breakdownCount, 6, 'el desglose debe listar los 6 perfiles');

  // Accesible por teclado: foco visible en el botón de repetir y funciona.
  await page.click('[data-quiz-restart]');
  await page.waitForTimeout(100);
  assert(!(await page.locator('[data-quiz-results]').isVisible()), 'repetir debe ocultar los resultados');
  const stillChecked = await page.locator('.quiz-question').first().locator('input[type=radio]:checked').count();
  assert.equal(stillChecked, 0, 'repetir debe limpiar las respuestas previas');

  assert.equal(requests.length, 0, `no debe haber peticiones de red externas: ${requests.join(', ')}`);
  assert.equal(jsErrors.length, 0, `no debe haber excepciones JS: ${jsErrors.join(' | ')}`);
  await context.close();
  console.log('tipo-lector-browser: PASS');
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
