// Smoke cross-engine (K.3, 2026-08-23): un conjunto representativo de
// rutas criticas se carga y es utilizable en Chromium, Firefox y WebKit.
// Ver docs/compatibilidad-cross-browser.md para el contrato completo.
//
// Uso:
//   node qa/cross-engine-smoke.mjs                # los 3 motores instalados
//   node qa/cross-engine-smoke.mjs --engines=chromium
//   QA_CHROMIUM_EXECUTABLE_PATH=... node qa/cross-engine-smoke.mjs --engines=chromium
import assert from 'node:assert/strict';
import { chromium, firefox, webkit } from 'playwright';
import { createServer } from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const MIME = new Map([
  ['.html', 'text/html; charset=utf-8'], ['.css', 'text/css; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'], ['.mjs', 'text/javascript; charset=utf-8'],
  ['.webp', 'image/webp'], ['.png', 'image/png'], ['.jpg', 'image/jpeg'],
  ['.svg', 'image/svg+xml'], ['.woff2', 'font/woff2'], ['.ico', 'image/x-icon'],
  ['.json', 'application/json; charset=utf-8'],
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

const ROUTES = [
  '/',
  '/las-manecillas-del-recuerdo/',
  '/las-manecillas-del-recuerdo/fragmentos/',
  '/libros/samuel-entre-mundos/',
  '/cuaderno/',
  '/recomendaciones/',
  '/recomendaciones/portal-fantasy-espanol/',
  '/herramientas/',
  '/herramientas/legibilidad/',
  '/asistente/',
];

const ENGINE_LAUNCHERS = { chromium, firefox, webkit };

function parseEngines() {
  const arg = process.argv.find((a) => a.startsWith('--engines='));
  if (!arg) return ['chromium', 'firefox', 'webkit'];
  return arg.split('=')[1].split(',').map((s) => s.trim()).filter(Boolean);
}

async function blockExternalNetwork(page) {
  await page.route(/gc\.zgo\.at/, (route) => route.abort());
  await page.route(/metricool\.com/, (route) => route.abort());
  await page.route(/workers\.dev/, (route) => route.abort());
  await page.route(/^https?:\/\/(?!127\.0\.0\.1)/, (route) => {
    const url = route.request().url();
    if (url.startsWith(ORIGIN)) return route.continue();
    route.abort();
  });
}

async function ensureExploreTriggerVisible(page, trigger) {
  if (await trigger.isVisible().catch(() => false)) return true;
  // Home V3 sigue la referencia LRB: en estado expandido el hamburger no se
  // muestra; aparece al superar el umbral de cabecera compacta. El smoke debe
  // probar el estado real donde ese control existe visualmente, no forzar una
  // decisión de diseño antigua que lo exigía ya en top=0.
  await page.evaluate(() => window.scrollTo(0, 360));
  await page.waitForTimeout(220);
  return trigger.isVisible().catch(() => false);
}

async function checkRoute(page, engineName, routePath) {
  const errors = [];
  const jsErrors = [];
  page.on('pageerror', (err) => jsErrors.push(String(err)));

  const response = await page.goto(`${ORIGIN}${routePath}`, { waitUntil: 'domcontentloaded', timeout: 20000 }).catch((e) => {
    errors.push(`goto falló: ${e.message}`);
    return null;
  });
  if (response && !response.ok()) errors.push(`HTTP ${response.status()} al cargar la ruta`);

  // Regression guard for the physical-iPhone Safari freeze fixed in #163.
  // The cross-engine smoke used to click "Entrar" immediately and therefore
  // could stay green even if the problematic WebM source was reintroduced.
  // Keep this deliberately structural: real iPhone playback remains a manual
  // hardware gate, but CI now protects the exact media-source contract that
  // avoids Safari selecting the bad source before the MP4 fallback.
  if (routePath === '/') {
    const videos = page.locator('[data-hero-video]');
    const videoCount = await videos.count();
    if (videoCount !== 1) {
      errors.push(`HOME intro debe tener exactamente 1 [data-hero-video], tiene ${videoCount}`);
    } else {
      const media = await videos.first().evaluate((video) => ({
        muted: video.muted,
        playsInline: video.playsInline,
        preload: video.preload,
        poster: video.getAttribute('poster') || '',
        sources: Array.from(video.querySelectorAll('source')).map((source) => ({
          src: source.getAttribute('src') || '',
          type: source.getAttribute('type') || '',
        })),
      }));
      if (!media.muted) errors.push('HOME intro pierde muted');
      if (!media.playsInline) errors.push('HOME intro pierde playsinline');
      if (media.preload !== 'auto') errors.push(`HOME intro preload inesperado: ${media.preload || '(vacío)'}`);
      if (!media.poster) errors.push('HOME intro pierde poster/fallback visual');
      if (media.sources.length !== 1) errors.push(`HOME intro debe conservar 1 source MP4, tiene ${media.sources.length}`);
      const source = media.sources[0];
      if (source && source.type !== 'video/mp4') errors.push(`HOME intro source type inesperado: ${source.type || '(vacío)'}`);
      if (source && !/hero-tinta-david-porto\.mp4(?:\?|$)/.test(source.src)) errors.push(`HOME intro source no apunta al MP4 canónico: ${source.src}`);
      if (media.sources.some((item) => /webm/i.test(item.type) || /\.webm(?:\?|$)/i.test(item.src))) {
        errors.push('HOME intro reintroduce WebM y reabre la regresión Safari/iPhone');
      }
    }
  }

  const introEnter = page.locator('[data-intro-enter]').first();
  if ((await introEnter.count()) > 0) {
    await introEnter.click();
    await page.waitForTimeout(900);
  }

  const header = await page.locator('header.site-header, header').first();
  if ((await header.count()) === 0) errors.push('no existe header de navegación');

  const navLinks = page.locator('.primary-nav a, nav[aria-label="Navegación principal"] a');
  const navCount = await navLinks.count();
  for (let i = 0; i < navCount; i++) {
    const href = await navLinks.nth(i).getAttribute('href');
    if (!href) errors.push(`enlace de navegación #${i} sin href`);
  }

  const exploreTrigger = page.locator('[data-explore-open]').first();
  if ((await exploreTrigger.count()) === 0) {
    errors.push('no existe el trigger [data-explore-open] de Explorar');
  } else if (!(await ensureExploreTriggerVisible(page, exploreTrigger))) {
    errors.push('el trigger de Explorar existe pero no llega a ser visible en su estado compacto');
  } else {
    await exploreTrigger.click();
    await page.waitForTimeout(150);
    const dialog = page.locator('[data-explore-dialog]');
    const isOpen = await dialog.evaluate((el) => el.open).catch(() => false);
    if (!isOpen) errors.push('el diálogo Explorar no queda abierto tras el clic');
    const focused = await page.evaluate(() => document.activeElement?.closest('[data-explore-dialog]') != null);
    if (!focused) errors.push('el foco no entra en el diálogo Explorar al abrirlo');
    const closeBtn = page.locator('[data-explore-close]').first();
    if ((await closeBtn.count()) > 0) {
      await closeBtn.click();
      await page.waitForTimeout(150);
      const stillOpen = await dialog.evaluate((el) => el.open).catch(() => false);
      if (stillOpen) errors.push('el diálogo Explorar no cierra al pulsar cerrar');
    }
  }

  await page.setViewportSize({ width: 375, height: 812 });
  await page.waitForTimeout(100);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  if (overflow > 1) errors.push(`overflow horizontal móvil: ${overflow}px`);
  await page.setViewportSize({ width: 1280, height: 800 });

  const forms = page.locator('form');
  const formCount = await forms.count();
  for (let i = 0; i < formCount; i++) {
    const submit = forms.nth(i).locator('button[type="submit"], input[type="submit"]').first();
    if ((await submit.count()) > 0) {
      const disabled = await submit.isDisabled().catch(() => false);
      if (disabled) errors.push(`formulario #${i} tiene su botón de envío deshabilitado por defecto`);
    }
  }

  if (jsErrors.length > 0) errors.push(`excepciones JS no capturadas: ${jsErrors.slice(0, 3).join(' | ')}`);
  return errors;
}

async function main() {
  const engines = parseEngines();
  const results = [];

  for (const engineName of engines) {
    const launcher = ENGINE_LAUNCHERS[engineName];
    if (!launcher) throw new Error(`Motor desconocido: ${engineName}`);
    const launchOpts = { headless: true };
    if (engineName === 'chromium' && process.env.QA_CHROMIUM_EXECUTABLE_PATH) {
      launchOpts.executablePath = process.env.QA_CHROMIUM_EXECUTABLE_PATH;
    }
    const browser = await launcher.launch(launchOpts);
    try {
      for (const routePath of ROUTES) {
        const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
        const page = await context.newPage();
        await blockExternalNetwork(page);
        const errors = await checkRoute(page, engineName, routePath);
        await context.close();
        if (errors.length > 0) results.push({ engineName, routePath, errors });
        console.log(`${errors.length === 0 ? 'ok  ' : 'FAIL'} [${engineName}] ${routePath}${errors.length ? ' -> ' + errors.join('; ') : ''}`);
      }
    } finally {
      await browser.close();
    }
  }

  server.close();
  if (results.length > 0) {
    console.error(`\ncross-engine-smoke: ${results.length} fallo(s)`);
    process.exitCode = 1;
    return;
  }
  console.log('\ncross-engine-smoke: PASS');
}

main().catch((err) => {
  console.error(err);
  server.close();
  process.exitCode = 1;
});
