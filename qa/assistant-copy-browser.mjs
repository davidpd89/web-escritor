// Verifica en un navegador real que el asistente arranca con la copy
// canonica (assets/assistant-copy.js) y que la interaccion basica sigue
// funcionando tras L.2 (2026-08-23).
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const MIME = new Map([
  ['.html', 'text/html; charset=utf-8'], ['.css', 'text/css; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'], ['.mjs', 'text/javascript; charset=utf-8'],
  ['.webp', 'image/webp'], ['.png', 'image/png'], ['.svg', 'image/svg+xml'],
  ['.woff2', 'font/woff2'], ['.ico', 'image/x-icon'], ['.json', 'application/json; charset=utf-8'],
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
  await page.route(/gc\.zgo\.at/, (r) => r.abort());
  await page.route(/challenges\.cloudflare\.com/, (r) => r.abort());
  await page.route(/\/api\/assistant/, (r) => r.abort());

  await page.goto(`${ORIGIN}/asistente/`, { waitUntil: 'load' });
  await page.waitForTimeout(200);

  // 1) Tras el arranque de JS, el H1 usa la copy canonica.
  const h1 = await page.locator('.tool-hero h1').textContent();
  assert.equal(h1, '¿Qué buscas?', 'el H1 debe usar la copy canonica tras inicializar');

  // 2) El composer usa el placeholder canonico.
  const placeholder = await page.locator('[data-assistant-query]').getAttribute('placeholder');
  assert.equal(placeholder, 'Escribe tu pregunta…', 'el placeholder debe usar la copy canonica');

  // 3) El boton de enviar tiene el aria-label canonico.
  const sendAriaLabel = await page.locator('[data-assistant-submit]').getAttribute('aria-label');
  assert.equal(sendAriaLabel, 'Enviar pregunta', 'el boton de enviar debe usar el aria-label canonico');

  // 4) El mensaje de bienvenida canonico aparece en el log de chat.
  const welcome = await page.locator('[data-assistant-log] .assistant-message__bubble p').first().textContent();
  assert.equal(welcome, 'Hola. Dime qué buscas y te ayudo a encontrarlo en la web.', 'el mensaje de bienvenida debe usar la copy canonica');

  // 5) Interaccion basica: escribir y enviar una pregunta no rompe nada
  //    (con el endpoint remoto bloqueado, cae al fallback local sin excepciones).
  await page.fill('[data-assistant-query]', '¿Dónde leo un fragmento gratis?');
  await page.click('[data-assistant-submit]');
  await page.waitForTimeout(800);
  const messages = await page.locator('[data-assistant-log] .assistant-message').count();
  assert(messages >= 2, 'debe aparecer al menos el mensaje del usuario y una respuesta');

  assert.equal(jsErrors.length, 0, `no debe haber excepciones JS: ${jsErrors.join(' | ')}`);

  await context.close();
  console.log('assistant-copy-browser: PASS');
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
