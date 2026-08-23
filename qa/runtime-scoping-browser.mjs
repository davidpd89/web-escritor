// Browser QA for PR #61 runtime scoping/focus contracts.
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const MIME = new Map([
  ['.html', 'text/html; charset=utf-8'], ['.css', 'text/css; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'], ['.mjs', 'text/javascript; charset=utf-8'],
  ['.webp', 'image/webp'], ['.png', 'image/png'],
  ['.jpg', 'image/jpeg'], ['.svg', 'image/svg+xml'], ['.woff2', 'font/woff2'], ['.ico', 'image/x-icon'],
]);
const server = createServer((req, res) => {
  const url = new URL(req.url, 'http://127.0.0.1');
  let clean;
  try { clean = decodeURIComponent(url.pathname.split('?')[0]).replace(/^\/+/, ''); }
  catch { res.writeHead(400); res.end(); return; }
  const file = path.join(ROOT, clean.endsWith('/') || clean === '' ? clean + 'index.html' : clean);
  if (!file.startsWith(ROOT) || !fs.existsSync(file) || !fs.statSync(file).isFile()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': MIME.get(path.extname(file).toLowerCase()) || 'application/octet-stream' });
  res.end(fs.readFileSync(file));
});
await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const ORIGIN = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

function watch(page, label) {
  const pageErrors = [];
  const consoleErrors = [];
  page.on('pageerror', (error) => pageErrors.push(error.message));
  page.on('console', (msg) => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });
  return () => {
    const appErrors = consoleErrors.filter((text) => !/Failed to load resource/i.test(text));
    assert.deepEqual(pageErrors, [], `${label}: pageerror: ${pageErrors.join(' | ')}`);
    assert.deepEqual(appErrors, [], `${label}: console error: ${appErrors.join(' | ')}`);
  };
}

async function noOverflow(page, label) {
  const [scrollWidth, clientWidth] = await page.evaluate(() => [document.documentElement.scrollWidth, document.documentElement.clientWidth]);
  assert(scrollWidth <= clientWidth + 1, `${label}: overflow horizontal ${scrollWidth}/${clientWidth}`);
}

async function scrollRatio(page, ratio) {
  await page.evaluate((value) => {
    const max = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
    window.scrollTo(0, Math.floor(max * value));
  }, ratio);
  await page.waitForTimeout(120);
}

async function assertFocusInside(page, selector, presses = 8) {
  for (let i = 0; i < presses; i += 1) {
    await page.keyboard.press('Tab');
    const inside = await page.evaluate((sel) => {
      const container = document.querySelector(sel);
      return Boolean(container && container.contains(document.activeElement));
    }, selector);
    assert(inside, `Tab ${i + 1}: el foco escapó de ${selector}`);
  }
}

try {
  // Popup desktop: 70%, CSS scoped, focus inicial, ciclo nativo, Escape y retorno.
  {
    const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    const page = await context.newPage();
    const verify = watch(page, 'newsletter-desktop');
    const requests = [];
    page.on('request', (req) => requests.push(req.url()));
    await page.goto(`${ORIGIN}/cuaderno/`, { waitUntil: 'networkidle' });
    assert(requests.some((url) => url.endsWith('/assets/newsletter-popup.js')));
    assert(requests.some((url) => url.endsWith('/assets/newsletter-popup.css')));
    assert(!requests.some((url) => url.includes('samuel-buy-modal')));

    const originFocus = page.locator('[data-explore-open]');
    await originFocus.focus();
    await scrollRatio(page, 0.65);
    assert.equal(await page.locator('#nl-popup-dialog[open]').count(), 0, 'popup no debe abrir antes del 70%');
    await scrollRatio(page, 0.72);
    await page.locator('#nl-popup-dialog[open]').waitFor({ state: 'visible' });
    assert.equal(await page.evaluate(() => document.activeElement?.id), 'nl-popup-email', 'foco inicial debe ir al email');
    await assertFocusInside(page, '#nl-popup-dialog', 8);
    await page.keyboard.press('Escape');
    await page.waitForFunction(() => !document.querySelector('#nl-popup-dialog'));
    assert.equal(await page.evaluate(() => document.activeElement?.matches('[data-explore-open]')), true, 'Escape debe devolver foco al origen');
    await scrollRatio(page, 0.1);
    await scrollRatio(page, 0.8);
    assert.equal(await page.locator('#nl-popup-dialog').count(), 0, 'no debe registrar/disparar un segundo popup en la misma carga');
    verify();
    await context.close();
  }

  // Si Explorar ya es modal, newsletter espera; al cerrarlo puede abrir después.
  {
    const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    const page = await context.newPage();
    const verify = watch(page, 'newsletter-no-stack');
    await page.goto(`${ORIGIN}/cuaderno/`, { waitUntil: 'load' });
    await page.locator('[data-explore-open]').click();
    await page.locator('[data-explore-dialog][open]').waitFor({ state: 'visible' });
    await scrollRatio(page, 0.75);
    assert.equal(await page.locator('#nl-popup-dialog[open]').count(), 0, 'newsletter no debe apilarse sobre Explorar');
    await page.keyboard.press('Escape');
    await page.locator('[data-explore-dialog]').waitFor({ state: 'hidden' });
    await scrollRatio(page, 0.1);
    await scrollRatio(page, 0.75);
    await page.locator('#nl-popup-dialog[open]').waitFor({ state: 'visible' });
    verify();
    await context.close();
  }

  // Sin temporizador legacy de 30 s.
  {
    const context = await browser.newContext();
    await context.addInitScript(() => {
      const original = window.setTimeout.bind(window);
      window.__qaDelays = [];
      window.setTimeout = (fn, delay, ...args) => { window.__qaDelays.push(Number(delay)); return original(fn, delay, ...args); };
    });
    const page = await context.newPage();
    await page.goto(`${ORIGIN}/cuaderno/`, { waitUntil: 'load' });
    await page.waitForTimeout(150);
    assert(!(await page.evaluate(() => window.__qaDelays)).includes(30000), 'no debe existir timer de 30 s');
    await context.close();
  }

  // Touch: no exit-intent. Desktop/fine pointer: sí.
  {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true });
    await context.addInitScript(() => {
      const original = window.matchMedia.bind(window);
      window.matchMedia = (query) => query === '(hover: hover) and (pointer: fine)'
        ? { media: query, matches: false, addEventListener(){}, removeEventListener(){} }
        : original(query);
    });
    const page = await context.newPage();
    await page.goto(`${ORIGIN}/cuaderno/`, { waitUntil: 'load' });
    await page.evaluate(() => document.dispatchEvent(new MouseEvent('mouseleave', { bubbles: true, clientY: 0 })));
    await page.waitForTimeout(120);
    assert.equal(await page.locator('#nl-popup-dialog[open]').count(), 0, 'touch no debe disparar exit-intent');
    await context.close();
  }
  {
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.goto(`${ORIGIN}/cuaderno/`, { waitUntil: 'load' });
    await page.evaluate(() => document.dispatchEvent(new MouseEvent('mouseleave', { bubbles: true, clientY: 0 })));
    await page.waitForTimeout(120);
    assert.equal(await page.locator('#nl-popup-dialog[open]').count(), 1, 'fine pointer debe conservar exit-intent');
    await context.close();
  }

  // Samuel: JS+CSS solo aquí, diálogo nativo, foco/restauración y una sola instancia.
  {
    const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    const page = await context.newPage();
    const verify = watch(page, 'samuel-modal');
    const requests = [];
    page.on('request', (req) => requests.push(req.url()));
    await page.goto(`${ORIGIN}/libros/samuel-entre-mundos/`, { waitUntil: 'networkidle' });
    assert(requests.some((url) => url.endsWith('/assets/samuel-buy-modal.js')), 'Samuel debe cargar JS modal');
    assert(requests.some((url) => url.endsWith('/assets/samuel-buy-modal.css')), 'Samuel debe cargar CSS modal');
    assert(!requests.some((url) => url.includes('newsletter-popup')), 'Samuel no debe cargar popup newsletter');

    const trigger = page.locator('[data-buy-modal]').first();
    await trigger.focus();
    await trigger.click();
    await page.locator('#buy-dialog[open]').waitFor({ state: 'visible' });
    assert.equal(await page.evaluate(() => document.activeElement?.classList.contains('buy-option--primary')), true, 'modal Samuel debe enfocar opción principal');
    await assertFocusInside(page, '#buy-dialog', 8);
    await page.keyboard.press('Escape');
    await page.locator('#buy-dialog').waitFor({ state: 'hidden' });
    assert.equal(await page.evaluate(() => document.activeElement?.hasAttribute('data-buy-modal')), true, 'Samuel debe restaurar foco al trigger');

    await trigger.click();
    await page.locator('#buy-dialog[open]').waitFor({ state: 'visible' });
    assert.equal(await page.locator('#buy-dialog').count(), 1, 'reapertura no debe duplicar dialog/listeners');
    await page.keyboard.press('Escape');

    await page.locator('[data-explore-open]').click();
    await page.locator('[data-explore-dialog][open]').waitFor({ state: 'visible' });
    await page.evaluate(() => document.querySelector('[data-buy-modal]')?.click());
    await page.waitForTimeout(80);
    assert.equal(await page.locator('#buy-dialog[open]').count(), 0, 'modal Samuel no debe apilarse sobre Explorar');
    verify();
    await context.close();
  }

  // Fail-closed: incluso si el asset Samuel se carga por accidente en Home.
  {
    const context = await browser.newContext();
    const page = await context.newPage();
    const requests = [];
    page.on('request', (req) => requests.push(req.url()));
    await page.goto(`${ORIGIN}/`, { waitUntil: 'load' });
    assert(!requests.some((url) => url.includes('newsletter-popup')), 'Home no carga popup');
    assert(!requests.some((url) => url.includes('samuel-buy-modal')), 'Home no carga modal Samuel');
    await page.evaluate(async () => {
      const fake = document.createElement('main');
      fake.dataset.family = 'book-samuel';
      fake.innerHTML = '<button type="button" data-buy-modal>Fake</button>';
      document.body.appendChild(fake);
      await new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = '/assets/samuel-buy-modal.js';
        script.onload = resolve;
        script.onerror = reject;
        document.body.appendChild(script);
      });
      fake.querySelector('[data-buy-modal]').click();
    });
    assert.equal(await page.locator('#buy-dialog').count(), 0, 'asset Samuel fuera de URL debe quedar inerte');
    assert.equal(await page.locator('link[data-samuel-buy-modal-style]').count(), 0, 'fuera de Samuel tampoco debe cargar CSS específico');
    await context.close();
  }

  // Volver arriba es opt-in (data-back-to-top, mismo contrato que
  // data-reading-progress): la home no lo lleva, una página larga sí.
  {
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.goto(`${ORIGIN}/`, { waitUntil: 'load' });
    assert.equal(await page.locator('.back-to-top').count(), 0, 'home no debe inyectar back-to-top sin opt-in');
    await context.close();
  }

  // Volver arriba es inmediato en el mismo turno y respeta reduced motion.
  for (const [motion, expected] of [['no-preference', 'smooth'], ['reduce', 'auto']]) {
    const context = await browser.newContext({ reducedMotion: motion });
    const page = await context.newPage();
    await page.goto(`${ORIGIN}/fragmento/`, { waitUntil: 'load' });
    const result = await page.evaluate(() => {
      const calls = [];
      window.scrollTo = (options) => calls.push(options);
      document.querySelector('.back-to-top')?.click();
      return calls;
    });
    assert.equal(result.length, 1, `back-to-top (${motion}) debe ejecutar scrollTo en el mismo turno`);
    assert.equal(result[0].behavior, expected, `back-to-top (${motion}) behavior incorrecto`);
    await context.close();
  }

  // 320 px, reduced motion y no-JS: sin reflow horizontal ni runtime ficticio.
  {
    const context = await browser.newContext({ viewport: { width: 320, height: 800 }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    await page.goto(`${ORIGIN}/cuaderno/`, { waitUntil: 'load' });
    await scrollRatio(page, 0.75);
    await page.locator('#nl-popup-dialog[open]').waitFor({ state: 'visible' });
    await noOverflow(page, 'popup-320');
    const animation = await page.locator('#nl-popup-dialog').evaluate((el) => getComputedStyle(el).animationDuration);
    assert(parseFloat(animation) < 0.001, `reduced motion popup: ${animation}`);
    await context.close();
  }
  {
    const context = await browser.newContext({ viewport: { width: 320, height: 800 } });
    const page = await context.newPage();
    await page.goto(`${ORIGIN}/libros/samuel-entre-mundos/`, { waitUntil: 'load' });
    await page.locator('[data-buy-modal]').first().click();
    await page.locator('#buy-dialog[open]').waitFor({ state: 'visible' });
    await noOverflow(page, 'samuel-modal-320');
    await context.close();
  }
  for (const route of ['/cuaderno/', '/libros/samuel-entre-mundos/']) {
    const context = await browser.newContext({ viewport: { width: 320, height: 800 }, javaScriptEnabled: false });
    const page = await context.newPage();
    await page.goto(`${ORIGIN}${route}`, { waitUntil: 'load' });
    assert(await page.locator('main').isVisible(), `${route}: main debe existir sin JS`);
    await noOverflow(page, `no-js-${route}`);
    assert.equal(await page.locator('#nl-popup-dialog,#buy-dialog').count(), 0, `${route}: no debe fingir modal sin JS`);
    await context.close();
  }

  console.log('runtime-scoping-browser: PASS');
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
