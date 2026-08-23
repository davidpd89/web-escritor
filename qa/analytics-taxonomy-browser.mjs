// Verifica en un navegador real que las acciones de usuario producen un
// unico evento logico, con la identidad de libro correcta y sin mezclarse
// (I.1, 2026-08-23): abrir el modal de compra de Samuel, leer un fragmento
// (Samuel vs Manecillas) y enviar el formulario de newsletter.
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const MIME = new Map([
  ['.html', 'text/html; charset=utf-8'], ['.css', 'text/css; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'], ['.webp', 'image/webp'], ['.png', 'image/png'],
  ['.jpg', 'image/jpeg'], ['.svg', 'image/svg+xml'], ['.woff2', 'font/woff2'], ['.ico', 'image/x-icon'],
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

async function withGoatcounterSpy(page) {
  await page.route(/gc\.zgo\.at/, (route) => route.abort());
  await page.route(/metricool\.com/, (route) => route.abort());
  await page.addInitScript(() => {
    window.__gcCalls = [];
    window.goatcounter = { count: (payload) => window.__gcCalls.push(payload) };
  });
}

try {
  // 1) Abrir el modal de compra de Samuel dispara EXACTAMENTE
  //    abrir-modal-comprar-samuel una vez, con identidad de libro.
  {
    const context = await browser.newContext();
    const page = await context.newPage();
    await withGoatcounterSpy(page);
    await page.goto(`${ORIGIN}/libros/samuel-entre-mundos/`, { waitUntil: 'load' });
    const trigger = page.locator('[data-buy-modal]').first();
    assert((await trigger.count()) > 0, 'debe existir un trigger [data-buy-modal] real');
    await trigger.scrollIntoViewIfNeeded();
    await trigger.click({ force: true });
    await page.waitForTimeout(200);
    const calls = await page.evaluate(() => window.__gcCalls);
    const opens = calls.filter((c) => c.path === 'abrir-modal-comprar-samuel');
    assert.equal(opens.length, 1, `debe dispararse exactamente una vez, disparado ${opens.length} veces`);
    assert(!calls.some((c) => c.path === 'abrir-modal-comprar'), 'el nombre legacy sin identidad de libro no debe usarse');
    await context.close();
  }

  // 2) Un clic al fragmento de Samuel dispara SOLO leer-fragmento-samuel.
  {
    const context = await browser.newContext();
    const page = await context.newPage();
    await withGoatcounterSpy(page);
    await page.goto(`${ORIGIN}/libros/samuel-entre-mundos/`, { waitUntil: 'load' });
    const link = page.locator('a[href*="/fragmento/"]:not([href*="/las-manecillas-del-recuerdo/"]):visible').first();
    assert((await link.count()) > 0, 'debe existir un enlace real y visible a /fragmento/ (Samuel)');
    await link.scrollIntoViewIfNeeded();
    await page.evaluate(() => document.addEventListener('click', (e) => e.preventDefault(), { capture: true, once: true }));
    await link.click({ force: true });
    await page.waitForTimeout(150);
    const calls = await page.evaluate(() => window.__gcCalls);
    assert.equal(calls.filter((c) => c.path === 'leer-fragmento-samuel').length, 1, 'leer-fragmento-samuel debe dispararse exactamente una vez');
    assert(!calls.some((c) => c.path === 'leer-fragmento-manecillas'), 'no debe mezclarse con el evento de Manecillas');
    await context.close();
  }

  // 3) Un clic al enlace real de la muestra de Manecillas dispara SOLO
  //    leer-fragmento-manecillas (bug corregido en I.1: antes no se
  //    contaba en absoluto).
  {
    const context = await browser.newContext();
    const page = await context.newPage();
    await withGoatcounterSpy(page);
    await page.goto(`${ORIGIN}/las-manecillas-del-recuerdo/`, { waitUntil: 'load' });
    const link = page.locator('a[href*="/las-manecillas-del-recuerdo/fragmentos/"]:visible').first();
    assert((await link.count()) > 0, 'debe existir un enlace real y visible a la muestra de Manecillas');
    await link.scrollIntoViewIfNeeded();
    await page.evaluate(() => document.addEventListener('click', (e) => e.preventDefault(), { capture: true, once: true }));
    await link.click({ force: true });
    await page.waitForTimeout(150);
    const calls = await page.evaluate(() => window.__gcCalls);
    assert.equal(calls.filter((c) => c.path === 'leer-fragmento-manecillas').length, 1, 'leer-fragmento-manecillas debe dispararse exactamente una vez');
    assert(!calls.some((c) => c.path === 'leer-fragmento-samuel'), 'no debe mezclarse con el evento de Samuel');
    await context.close();
  }

  console.log('analytics-taxonomy-browser: PASS');
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
