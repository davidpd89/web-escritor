// Verifica el contrato del funnel de muestra de Las manecillas del
// recuerdo (H.2, 2026-08-23): eventos con identidad de libro, sin doble
// conteo, sin mezclarse con el funnel de Samuel, y sin ningun evento de
// compra mientras no exista tienda real.
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

// Espia goatcounter.count() sin red real: _gcEvent solo llama a
// window.goatcounter.count si existe, asi que basta con proveerlo antes
// de que corra ningun script de la pagina. Fundamental bloquear la carga
// real de //gc.zgo.at/count.js: si el entorno tiene salida a internet, ese
// script real termina cargando en paralelo y SOBRESCRIBE window.goatcounter
// a mitad de test (con su propio cliente, que ademas descarta eventos en
// localhost) -- carrera real que se detecto ejecutando este test de verdad,
// no una hipotesis.
async function withGoatcounterSpy(page) {
  await page.route(/gc\.zgo\.at/, (route) => route.abort());
  await page.route(/metricool\.com/, (route) => route.abort());
  await page.addInitScript(() => {
    window.__gcCalls = [];
    window.goatcounter = { count: (payload) => window.__gcCalls.push(payload) };
  });
}

try {
  // 1) sample-start-manecillas se dispara al entrar en el primer fragmento.
  {
    const context = await browser.newContext();
    const page = await context.newPage();
    await withGoatcounterSpy(page);
    await page.goto(`${ORIGIN}/las-manecillas-del-recuerdo/fragmentos/`, { waitUntil: 'load' });
    await page.waitForTimeout(400);
    const calls = await page.evaluate(() => window.__gcCalls);
    const starts = calls.filter((c) => c.path === 'sample-start-manecillas');
    assert.equal(starts.length, 1, `sample-start-manecillas debe dispararse exactamente una vez, disparado ${starts.length} veces`);
    await context.close();
  }

  // 2) sample-complete-manecillas se dispara una sola vez al llegar al final,
  //    incluso si el observer vuelve a intersectar (scroll arriba y abajo).
  {
    const context = await browser.newContext();
    const page = await context.newPage();
    await withGoatcounterSpy(page);
    await page.goto(`${ORIGIN}/las-manecillas-del-recuerdo/fragmentos/`, { waitUntil: 'load' });
    await page.locator('#cta-final').scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(200);
    await page.locator('#cta-final').scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
    const calls = await page.evaluate(() => window.__gcCalls);
    const completes = calls.filter((c) => c.path === 'sample-complete-manecillas');
    assert.equal(completes.length, 1, `sample-complete-manecillas debe dispararse una unica vez incluso con scroll repetido, disparado ${completes.length} veces`);
    await context.close();
  }

  // 3) Ningun evento de compra para Manecillas (no hay tienda real todavia).
  {
    const context = await browser.newContext();
    const page = await context.newPage();
    await withGoatcounterSpy(page);
    await page.goto(`${ORIGIN}/las-manecillas-del-recuerdo/fragmentos/`, { waitUntil: 'load' });
    await page.locator('#cta-final').scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);
    const calls = await page.evaluate(() => window.__gcCalls);
    assert(!calls.some((c) => /buy-(open|click)-manecillas/.test(c.path)), 'no debe existir ningun evento buy-open/buy-click para Manecillas mientras no haya tienda real');
    await context.close();
  }

  // 4) El funnel de Samuel sigue diferenciado: un clic a /fragmento/ (Samuel)
  //    dispara leer-fragmento-samuel, no el evento de Manecillas.
  {
    const context = await browser.newContext();
    const page = await context.newPage();
    await withGoatcounterSpy(page);
    await page.goto(`${ORIGIN}/libros/samuel-entre-mundos/`, { waitUntil: 'load' });
    const link = page.locator('a[href*="/fragmento/"]:not([href*="/las-manecillas-del-recuerdo/"]):visible').first();
    assert((await link.count()) > 0, 'debe existir al menos un enlace real y visible a /fragmento/ (Samuel) en su propia pagina');
    await link.scrollIntoViewIfNeeded();
    // El enlace no lleva preventDefault (navega de verdad, es un enlace
    // normal): se inyecta un listener en fase de CAPTURA que solo llama a
    // preventDefault() para evitar la navegacion real, sin impedir que el
    // listener real de script.js (fase de burbuja, se ejecuta despues de la
    // captura) siga disparando el evento con normalidad.
    await page.evaluate(() => document.addEventListener('click', (e) => e.preventDefault(), { capture: true, once: true }));
    await link.click({ force: true });
    await page.waitForTimeout(150);
    const calls = await page.evaluate(() => window.__gcCalls);
    assert(calls.some((c) => c.path === 'leer-fragmento-samuel'), 'el clic a /fragmento/ debe disparar leer-fragmento-samuel');
    assert(!calls.some((c) => c.path === 'leer-fragmento-manecillas'), 'el clic a /fragmento/ (Samuel) no debe disparar el evento de Manecillas');
    await context.close();
  }

  // 5) El enlace real a la muestra de Manecillas dispara leer-fragmento-manecillas.
  {
    const context = await browser.newContext();
    const page = await context.newPage();
    await withGoatcounterSpy(page);
    await page.goto(`${ORIGIN}/las-manecillas-del-recuerdo/`, { waitUntil: 'load' });
    const link = page.locator('a[href*="/las-manecillas-del-recuerdo/fragmentos/"]:visible').first();
    assert((await link.count()) > 0, 'debe existir al menos un enlace real y visible a la muestra de Manecillas en su propia ficha');
    await link.scrollIntoViewIfNeeded();
    await page.evaluate(() => document.addEventListener('click', (e) => e.preventDefault(), { capture: true, once: true }));
    await link.click({ force: true });
    await page.waitForTimeout(150);
    const calls = await page.evaluate(() => window.__gcCalls);
    assert(calls.some((c) => c.path === 'leer-fragmento-manecillas'), 'el clic al enlace real de la muestra debe disparar leer-fragmento-manecillas');
    await context.close();
  }

  console.log('manecillas-funnel-browser: PASS');
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
