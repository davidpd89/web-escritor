// La intro cinematica de la Home solo debe verse al entrar al sitio. Al volver
// a la Home (casita, atras, recarga, o llegando desde otra pagina del sitio)
// la capa .intro no debe pintarse ni un fotograma. Y "Entrar" debe estar
// disponible desde el principio, sin esperar al final del video.
// Uso: node qa/home-intro-return-no-flash.mjs [baseURL]   (por defecto levanta un servidor estatico)
import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {createServer} from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/(\w:)/, '$1')), '..');
const TYPES = {'.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.webp': 'image/webp', '.jpg': 'image/jpeg', '.png': 'image/png', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.mp4': 'video/mp4', '.xml': 'application/xml', '.webmanifest': 'application/manifest+json'};

function startServer() {
  const server = createServer((req, res) => {
    let rel = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    let file = path.join(ROOT, rel);
    if (!file.startsWith(ROOT)) { res.writeHead(403).end(); return; }
    if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
    if (!fs.existsSync(file)) { res.writeHead(404).end(); return; }
    res.writeHead(200, {'content-type': TYPES[path.extname(file)] || 'application/octet-stream', 'cache-control': 'no-store'});
    fs.createReadStream(file).pipe(res);
  });
  return new Promise((resolve) => server.listen(0, '127.0.0.1', () => resolve(server)));
}

// Registra en cada carga si .intro llego a tener display distinto de none en
// algun fotograma: se muestrea en requestAnimationFrame, que corre justo antes
// de cada pintado (no durante el parseo, cuando el CSS aun no aplica).
const PROBE = () => {
  window.__introPainted = false;
  const sample = () => {
    const el = document.querySelector('[data-intro]');
    if (el && getComputedStyle(el).display !== 'none' && el.getBoundingClientRect().height > 0) window.__introPainted = true;
  };
  const loop = () => { sample(); if (performance.now() < 4000) requestAnimationFrame(loop); };
  requestAnimationFrame(loop);
};

const server = process.argv[2] ? null : await startServer();
const base = process.argv[2] || `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch();
const results = [];
const check = (name, fn) => results.push(fn().then(() => console.log(`PASS ${name}`), (e) => { console.log(`FAIL ${name}: ${e.message}`); process.exitCode = 1; }));

try {
  const ctx = await browser.newContext({serviceWorkers: 'block'});
  await ctx.addInitScript(PROBE);
  const page = await ctx.newPage();
  const painted = () => page.evaluate(() => window.__introPainted);

  // 1. Primera visita: la intro se ve y "Entrar" esta visible en menos de 1,5 s.
  await page.goto(base + '/');
  await page.waitForTimeout(1200);
  const enterOpacity = await page.$eval('[data-intro-enter]', (b) => +getComputedStyle(b).opacity);
  await check('primera visita muestra la intro', async () => assert.equal(await painted(), true));
  await check('Entrar visible antes de 1,2 s', async () => assert.ok(enterOpacity > 0.9, `opacidad ${enterOpacity}`));
  await page.click('[data-intro-enter]');
  await page.waitForFunction(() => document.querySelector('[data-intro]').hidden, null, {timeout: 3000});

  // 2. Ir a otra pagina y volver con la casita/logo (enlace a "/").
  await page.goto(base + '/libros/');
  await page.evaluate(() => { const a = document.createElement('a'); a.href = '/'; a.id = 'qa-home'; a.textContent = 'Inicio'; a.style.cssText = 'position:fixed;top:0;left:0;z-index:99999;background:#fff;padding:8px'; document.body.append(a); });
  await page.click('#qa-home');
  await page.waitForLoadState('load');
  const p2 = await painted();
  await check('volver por enlace a la Home no pinta la intro', async () => assert.equal(p2, false));

  // 3. Atras (sin bfcache garantizado: Playwright suele recargar).
  await page.goto(base + '/libros/');
  await page.goBack();
  await page.waitForLoadState('load');
  const p3 = await painted();
  await check('atras hacia la Home no pinta la intro', async () => assert.equal(p3, false));

  // 4. Recarga de la Home.
  await page.reload();
  await page.waitForLoadState('load');
  const p4 = await painted();
  await check('recargar la Home no pinta la intro', async () => assert.equal(p4, false));
  await ctx.close();

  // 5. Visitante que entra por una subpagina y luego va a la Home.
  const ctx2 = await browser.newContext({serviceWorkers: 'block'});
  await ctx2.addInitScript(PROBE);
  const page2 = await ctx2.newPage();
  await page2.goto(base + '/libros/');
  await page2.evaluate(() => { const a = document.createElement('a'); a.href = '/'; a.id = 'qa-home'; a.textContent = 'Inicio'; a.style.cssText = 'position:fixed;top:0;left:0;z-index:99999;background:#fff;padding:8px'; document.body.append(a); });
  await page2.click('#qa-home');
  await page2.waitForLoadState('load');
  const p5 = await page2.evaluate(() => window.__introPainted);
  const locked = await page2.evaluate(() => document.documentElement.classList.contains('intro-lock'));
  await check('desde subpagina a la Home no hay intro ni bloqueo', async () => { assert.equal(p5, false); assert.equal(locked, false); });
  await ctx2.close();

  // 6. Nueva sesion entrando directo: vuelve a haber intro.
  const ctx3 = await browser.newContext({serviceWorkers: 'block'});
  await ctx3.addInitScript(PROBE);
  const page3 = await ctx3.newPage();
  await page3.goto(base + '/');
  await page3.waitForTimeout(300);
  const p6 = await page3.evaluate(() => window.__introPainted);
  await check('sesion nueva entrando directo ve la intro', async () => assert.equal(p6, true));
  await ctx3.close();

  await Promise.all(results);
} finally {
  await browser.close();
  server?.close();
}
