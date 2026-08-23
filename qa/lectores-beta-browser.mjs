// Verifica en un navegador real el flujo de alta de /lectores-beta/
// (N.1, 2026-08-23): consentimiento propio, envio con source="lectores-beta",
// y que NO reutiliza el copy de exito de la newsletter general.
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const MIME = new Map([
  ['.html', 'text/html; charset=utf-8'], ['.css', 'text/css; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'], ['.webp', 'image/webp'], ['.png', 'image/png'],
  ['.svg', 'image/svg+xml'], ['.woff2', 'font/woff2'], ['.ico', 'image/x-icon'],
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
  // 1) Sin consentimiento marcado: no debe enviarse la peticion.
  {
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.route(/gc\.zgo\.at/, (r) => r.abort());
    let workerCalled = false;
    await page.route(/subscribe\.davidpd89\.workers\.dev/, (route) => { workerCalled = true; route.abort(); });
    await page.goto(`${ORIGIN}/lectores-beta/`, { waitUntil: 'load' });
    await page.fill('#lectores-beta-email', 'beta@example.com');
    await page.click('#lectores-beta-form [type=submit]');
    await page.waitForTimeout(200);
    const status = await page.locator('#lectores-beta-status').textContent();
    assert.match(status || '', /consentimiento/i, 'debe pedir el consentimiento del programa de lectores beta, no el genérico de newsletter');
    assert.equal(workerCalled, false, 'no debe llamar al Worker sin consentimiento marcado');
    await context.close();
  }

  // 2) Con consentimiento marcado: envía { email, source: "lectores-beta" }
  //    y NO reutiliza el copy de éxito de la newsletter general.
  {
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.route(/gc\.zgo\.at/, (r) => r.abort());
    let requestBody = null;
    await page.route(/subscribe\.davidpd89\.workers\.dev/, (route) => {
      requestBody = route.request().postDataJSON();
      route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify({ ok: true }) });
    });
    await page.goto(`${ORIGIN}/lectores-beta/`, { waitUntil: 'load' });
    await page.fill('#lectores-beta-email', 'beta2@example.com');
    await page.check('#lectores-beta-gdpr');
    await page.click('#lectores-beta-form [type=submit]');
    await page.waitForTimeout(300);

    assert.deepEqual(requestBody, { email: 'beta2@example.com', source: 'lectores-beta' }, 'debe enviar exactamente { email, source: "lectores-beta" }');
    const successText = await page.locator('#lectores-beta-form').textContent();
    assert.match(successText || '', /lectores beta/i, 'el copy de éxito debe mencionar el programa de lectores beta, no la newsletter general');
    assert.doesNotMatch(successText || '', /novedades de David Porto Díaz/i, 'no debe reutilizar el copy de éxito de la newsletter general');
    await context.close();
  }

  console.log('lectores-beta-browser: PASS');
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
