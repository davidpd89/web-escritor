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
  // "Modo local/inactivo seguro": nada de red externa real durante el
  // smoke (GoatCounter, Metricool, Worker del asistente, etc.).
  await page.route(/gc\.zgo\.at/, (route) => route.abort());
  await page.route(/metricool\.com/, (route) => route.abort());
  await page.route(/workers\.dev/, (route) => route.abort());
  await page.route(/^https?:\/\/(?!127\.0\.0\.1)/, (route) => {
    // Cualquier otro host externo (fuentes de terceros, APIs, etc.) se
    // aborta; el smoke solo necesita el propio servidor local.
    const url = route.request().url();
    if (url.startsWith(ORIGIN)) return route.continue();
    route.abort();
  });
}

async function checkRoute(page, engineName, routePath) {
  const errors = [];
  const jsErrors = [];
  page.on('pageerror', (err) => jsErrors.push(String(err)));

  const response = await page.goto(`${ORIGIN}${routePath}`, { waitUntil: 'domcontentloaded', timeout: 20000 }).catch((e) => {
    errors.push(`goto falló: ${e.message}`);
    return null;
  });
  if (response && !response.ok()) {
    errors.push(`HTTP ${response.status()} al cargar la ruta`);
  }

  // Shell de navegación utilizable.
  const header = await page.locator('header.site-header, header').first();
  if ((await header.count()) === 0) errors.push('no existe header de navegación');

  // Enlaces criticos: primary-nav (si existe) deben tener href no vacio.
  const navLinks = page.locator('.primary-nav a, nav[aria-label="Navegación principal"] a');
  const navCount = await navLinks.count();
  for (let i = 0; i < navCount; i++) {
    const href = await navLinks.nth(i).getAttribute('href');
    if (!href) errors.push(`enlace de navegación #${i} sin href`);
  }

  // Explorar: abre, gestiona foco, cierra. Toda página con el shell v1
  // debe tener este trigger; si no existe, es un fallo, no un "no aplica".
  const exploreTrigger = page.locator('[data-explore-open]').first();
  if ((await exploreTrigger.count()) === 0) {
    errors.push('no existe el trigger [data-explore-open] de Explorar');
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

  // Overflow horizontal en viewport móvil representativo.
  await page.setViewportSize({ width: 375, height: 812 });
  await page.waitForTimeout(100);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  if (overflow > 1) errors.push(`overflow horizontal móvil: ${overflow}px`);
  await page.setViewportSize({ width: 1280, height: 800 });

  // Formularios esenciales no deshabilitados por completo.
  const forms = page.locator('form');
  const formCount = await forms.count();
  for (let i = 0; i < formCount; i++) {
    const submit = forms.nth(i).locator('button[type="submit"], input[type="submit"]').first();
    if ((await submit.count()) > 0) {
      const disabled = await submit.isDisabled().catch(() => false);
      if (disabled) errors.push(`formulario #${i} tiene su botón de envío deshabilitado por defecto`);
    }
  }

  if (jsErrors.length > 0) {
    errors.push(`excepciones JS no capturadas: ${jsErrors.slice(0, 3).join(' | ')}`);
  }

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
        if (errors.length > 0) {
          results.push({ engineName, routePath, errors });
        }
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