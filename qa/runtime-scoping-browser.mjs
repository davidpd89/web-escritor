// Verifica en un navegador real la extraccion de runtime scoping (H.1,
// 2026-08-23): el popup de newsletter y el modal de compra de Samuel salen
// de script.js a assets/newsletter-popup.js y assets/samuel-buy-modal.js
// respectivamente, cargados solo donde corresponde. Complementa a
// scripts/check-runtime-scoping.py (estatico) verificando comportamiento
// real: triggers, CSS externo aplicado, y que las paginas fuera de ambito
// no descargan nada de mas.
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

try {
  // 1) cuaderno/ (dentro de ambito del popup): assets correctos + triggers reales.
  {
    const context = await browser.newContext();
    const page = await context.newPage();
    const urls = [];
    page.on('request', (req) => urls.push(req.url()));
    await page.goto(`${ORIGIN}/cuaderno/`, { waitUntil: 'networkidle' });
    assert(urls.some((u) => u.endsWith('/assets/newsletter-popup.js')), 'cuaderno/ debe solicitar newsletter-popup.js');
    assert(urls.some((u) => u.endsWith('/assets/newsletter-popup.css')), 'cuaderno/ debe solicitar newsletter-popup.css');
    assert(!urls.some((u) => u.endsWith('/assets/samuel-buy-modal.js')), 'cuaderno/ no debe solicitar samuel-buy-modal.js');

    await page.evaluate(() => window.scrollTo(0, Math.floor(Math.max(1, document.documentElement.scrollHeight - window.innerHeight) * 0.65)));
    await page.waitForTimeout(200);
    assert.equal(await page.locator('#nl-popup-overlay').count(), 0, 'popup no debe aparecer antes del 70% de scroll');

    await page.evaluate(() => window.scrollTo(0, Math.floor(Math.max(1, document.documentElement.scrollHeight - window.innerHeight) * 0.72)));
    await page.waitForTimeout(300);
    assert.equal(await page.locator('#nl-popup-overlay').count(), 1, 'popup debe aparecer al superar el 70% de scroll');
    assert(await page.locator('#nl-popup-title').first().isVisible(), 'panel del popup visible con CSS externo aplicado');
    await context.close();
  }

  // 2) sin temporizador de 30s.
  {
    const context = await browser.newContext();
    await context.addInitScript(() => {
      const orig = window.setTimeout.bind(window);
      window.__delays = [];
      window.setTimeout = (fn, delay, ...a) => { window.__delays.push(Number(delay)); return orig(fn, delay, ...a); };
    });
    const page = await context.newPage();
    await page.goto(`${ORIGIN}/cuaderno/`, { waitUntil: 'load' });
    await page.waitForTimeout(300);
    const delays = await page.evaluate(() => window.__delays || []);
    assert(!delays.includes(30000), 'no debe registrarse el timer de 30s (retirado por spec)');
    await context.close();
  }

  // 3) home (fuera de ambito): no carga ni popup ni modal de Samuel.
  {
    const context = await browser.newContext();
    const page = await context.newPage();
    const urls = [];
    page.on('request', (req) => urls.push(req.url()));
    await page.goto(`${ORIGIN}/`, { waitUntil: 'networkidle' });
    assert(!urls.some((u) => u.includes('newsletter-popup')), 'home no debe cargar newsletter-popup (js ni css)');
    assert(!urls.some((u) => u.includes('samuel-buy-modal')), 'home no debe cargar samuel-buy-modal.js');
    await context.close();
  }

  // 4) pagina de Samuel: el modal extraido sigue funcionando end-to-end.
  {
    const context = await browser.newContext();
    const page = await context.newPage();
    const urls = [];
    page.on('request', (req) => urls.push(req.url()));
    await page.goto(`${ORIGIN}/libros/samuel-entre-mundos/`, { waitUntil: 'networkidle' });
    assert(urls.some((u) => u.endsWith('/assets/samuel-buy-modal.js')), 'la pagina de Samuel debe solicitar samuel-buy-modal.js');
    const trigger = page.locator('[data-buy-modal]').first();
    assert((await trigger.count()) > 0, 'debe existir un trigger [data-buy-modal] real');
    await trigger.scrollIntoViewIfNeeded();
    await trigger.click({ force: true });
    await page.waitForTimeout(200);
    assert.equal(await page.locator('#buy-dialog[open]').count(), 1, 'el dialog de compra debe abrirse al pulsar el trigger');
    await context.close();
  }

  // 5) exit-intent gateado a hover:hover + pointer:fine.
  {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true });
    await context.addInitScript(() => {
      const orig = window.matchMedia.bind(window);
      window.matchMedia = (q) => q === '(hover: hover) and (pointer: fine)'
        ? { media: q, matches: false, addEventListener(){}, removeEventListener(){} }
        : orig(q);
    });
    const page = await context.newPage();
    await page.goto(`${ORIGIN}/cuaderno/`, { waitUntil: 'load' });
    await page.waitForTimeout(200);
    await page.evaluate(() => document.dispatchEvent(new MouseEvent('mouseleave', { bubbles: true, clientY: 0 })));
    await page.waitForTimeout(200);
    assert.equal(await page.locator('#nl-popup-overlay').count(), 0, 'exit-intent no debe disparar sin hover:hover+pointer:fine');
    await context.close();
  }
  {
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.goto(`${ORIGIN}/cuaderno/`, { waitUntil: 'load' });
    await page.waitForTimeout(200);
    await page.evaluate(() => document.dispatchEvent(new MouseEvent('mouseleave', { bubbles: true, clientY: 0 })));
    await page.waitForTimeout(200);
    assert.equal(await page.locator('#nl-popup-overlay').count(), 1, 'exit-intent debe disparar con hover:hover+pointer:fine');
    await context.close();
  }

  console.log('runtime-scoping-browser: PASS');
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
