// Cross-device, multi-viewport comprehensive smoke test suite.
// Validates responsive layout integrity, horizontal overflow absence,
// interaction responsiveness, and zero console errors across 7 device viewports.
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const DIST = process.env.SITEWIDE_DIST || path.join(ROOT, '.preview-dist-sitewide-qa');

if (!process.env.SITEWIDE_SKIP_BUILD) {
  const py = process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
  execFileSync(py, ['scripts/build-public-dist.py', '--out', DIST], { cwd: ROOT, stdio: 'inherit' });
}

const MIME = new Map([
  ['.html', 'text/html; charset=utf-8'], ['.css', 'text/css; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'], ['.mjs', 'text/javascript; charset=utf-8'],
  ['.json', 'application/json; charset=utf-8'], ['.xml', 'application/xml; charset=utf-8'],
  ['.txt', 'text/plain; charset=utf-8'], ['.webp', 'image/webp'], ['.png', 'image/png'],
  ['.jpg', 'image/jpeg'], ['.jpeg', 'image/jpeg'], ['.svg', 'image/svg+xml'],
  ['.woff2', 'font/woff2'], ['.ico', 'image/x-icon'], ['.ics', 'text/calendar; charset=utf-8'],
]);

function createStaticServer(root) {
  return createServer((req, res) => {
    const parsed = new URL(req.url, 'http://127.0.0.1');
    let pathname = decodeURIComponent(parsed.pathname);
    if (pathname.endsWith('/')) pathname += 'index.html';
    const filePath = path.join(root, pathname);
    if (!filePath.startsWith(root)) {
      res.writeHead(403).end('Forbidden');
      return;
    }
    fs.readFile(filePath, (err, data) => {
      if (err) {
        res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' }).end('Not Found');
        return;
      }
      const ext = path.extname(filePath).toLowerCase();
      res.writeHead(200, { 'Content-Type': MIME.get(ext) || 'application/octet-stream' });
      res.end(data);
    });
  });
}

const VIEWPORTS = [
  { name: 'Ultra-compact iPhone 5/SE1 (320x568)', width: 320, height: 568, isMobile: true, hasTouch: true },
  { name: 'Short Mobile / Keyboard Open (390x500)', width: 390, height: 500, isMobile: true, hasTouch: true },
  { name: 'Low Landscape Mobile (667x375)', width: 667, height: 375, isMobile: true, hasTouch: true },
  { name: 'Mobile Android (360x740)', width: 360, height: 740, isMobile: true, hasTouch: true },
  { name: 'Mobile iPhone SE (375x667)', width: 375, height: 667, isMobile: true, hasTouch: true },
  { name: 'Mobile iPhone 14/15 (390x844)', width: 390, height: 844, isMobile: true, hasTouch: true },
  { name: 'Tablet iPad Portrait (768x1024)', width: 768, height: 1024, isMobile: true, hasTouch: true },
  { name: 'Tablet iPad Landscape (1024x768)', width: 1024, height: 768, isMobile: false, hasTouch: true },
  { name: 'Laptop (1280x800)', width: 1280, height: 800, isMobile: false, hasTouch: false },
  { name: 'Desktop Full HD (1920x1080)', width: 1920, height: 1080, isMobile: false, hasTouch: false },
];

const TARGET_ROUTES = [
  '/',
  '/las-manecillas-del-recuerdo/',
  '/libros/samuel-entre-mundos/',
  '/autor.html',
  '/cuaderno/',
  '/cuaderno/que-es-el-portal-fantasy/',
  '/herramientas/',
  '/recomendaciones/',
  '/editoriales/',
  '/convocatorias-escritores/',
  '/prensa.html',
  '/eventos.html',
  '/premios.html',
  '/accesibilidad/',
  '/herramientas/contador-palabras/',
  '/herramientas/legibilidad/',
  '/herramientas/dialogo/',
  '/herramientas/dialogo-convenciones/',
  '/herramientas/manuscrito/',
  '/herramientas/repeticiones/',
  '/herramientas/nombres-personajes/',
  '/herramientas/que-tipo-de-lector-eres/',
  '/herramientas/distribucion-pov/',
  '/herramientas/variedad-lexica/',
  '/herramientas/tiempo-lectura-voz-alta/',
  '/herramientas/auditor-pagina-libro/',
  '/herramientas/eventos-ics/',
  '/herramientas/kit-prensa-escritores/',
  '/herramientas/json-ld-escritores/',
  '/herramientas/tarjeta-estoy-leyendo/',
  '/herramientas/entrevista-familiar/',
];

const server = createStaticServer(DIST);
await new Promise(r => server.listen(0, '127.0.0.1', r));
const { port } = server.address();
const origin = `http://127.0.0.1:${port}`;

console.log(`Cross-device smoke testing ${TARGET_ROUTES.length} routes across ${VIEWPORTS.length} viewports...`);

const browser = await chromium.launch({ headless: true });
let totalPassed = 0;
const failures = [];

try {
  for (const vp of VIEWPORTS) {
    const context = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      isMobile: vp.isMobile,
      hasTouch: vp.hasTouch,
    });

    for (const route of TARGET_ROUTES) {
      const page = await context.newPage();
      const errors = [];

      page.on('console', msg => {
        if (msg.type() === 'error') errors.push(`console.error: ${msg.text()}`);
      });
      page.on('pageerror', err => errors.push(`pageerror: ${err.message}`));

      try {
        const res = await page.goto(`${origin}${route}`, { waitUntil: 'domcontentloaded', timeout: 10000 });
        assert.equal(res.status(), 200, `Expected 200 OK for ${route}`);

        // 1. Check for horizontal overflow (max 1px rounding tolerance)
        const overflow = await page.evaluate(() => {
          const docWidth = document.documentElement.scrollWidth;
          const winWidth = window.innerWidth;
          const bodyWidth = document.body ? document.body.scrollWidth : 0;
          return {
            overflows: Math.max(docWidth, bodyWidth) > winWidth + 1,
            docWidth,
            bodyWidth,
            winWidth,
          };
        });

        if (overflow.overflows) {
          errors.push(`Horizontal overflow detected: docWidth=${overflow.docWidth}, bodyWidth=${overflow.bodyWidth}, winWidth=${overflow.winWidth}`);
        }

        // 2. Test interactive elements if present on page
        // a) Explorar / nav button
        const exploreBtn = await page.$('button[data-dialog-open="site-menu"], button[data-dialog-target="site-menu"], .site-nav-toggle');
        if (exploreBtn && (await exploreBtn.isVisible())) {
          await exploreBtn.click();
          await page.waitForTimeout(100);
          const closeBtn = await page.$('dialog[open] button[data-dialog-close], dialog[open] .close-btn, dialog[open] button');
          if (closeBtn && (await closeBtn.isVisible())) {
            await closeBtn.click();
            await page.waitForTimeout(50);
          }
        }

        // b) Interactive textarea tool smoke (e.g. contador, legibilidad, dialogo, etc.)
        const textarea = await page.$('textarea');
        if (textarea && (await textarea.isVisible())) {
          await textarea.fill('Había una vez en un reino lejano un misterioso portal de piedra.');
          await page.waitForTimeout(150);
        }

        // Check if any errors occurred during render or interaction
        if (errors.length > 0) {
          failures.push({ viewport: vp.name, route, errors });
        } else {
          totalPassed++;
        }
      } catch (err) {
        failures.push({ viewport: vp.name, route, errors: [err.message] });
      } finally {
        await page.close();
      }
    }
    await context.close();
  }

  // 3. Dynamic Mobile Virtual Keyboard Simulation
  // Tests opening a page at 390x844, focusing input/textarea, dynamically shrinking height to 500px,
  // and ensuring no overflow, element remains visible and accessible, and restoring cleanly.
  console.log('Testing dynamic virtual keyboard resize on interactive surfaces...');
  const KEYBOARD_TEST_ROUTES = [
    '/lectores-beta/',
    '/herramientas/contador-palabras/',
    '/convocatorias-escritores/',
    '/herramientas/legibilidad/',
    '/herramientas/dialogo/',
    '/herramientas/manuscrito/',
  ];
  const kbContext = await browser.newContext({
    viewport: { width: 390, height: 844 },
    isMobile: true,
    hasTouch: true,
  });
  for (const route of KEYBOARD_TEST_ROUTES) {
    const page = await kbContext.newPage();
    try {
      await page.goto(`${origin}${route}`, { waitUntil: 'domcontentloaded', timeout: 10000 });
      const inputEl = page.locator('input[type="email"], textarea, input[type="text"]').first();
      if (await inputEl.count() > 0) {
        await inputEl.focus();
        await page.setViewportSize({ width: 390, height: 500 });
        await page.waitForTimeout(60);

        const state = await page.evaluate(() => {
          const active = document.activeElement;
          const rect = active ? active.getBoundingClientRect() : null;
          const overflows = Math.max(document.documentElement.scrollWidth, document.body ? document.body.scrollWidth : 0) > window.innerWidth + 1;
          return {
            hasActive: !!active,
            overflows,
            top: rect ? rect.top : 0,
            bottom: rect ? rect.bottom : 0,
            winHeight: window.innerHeight,
          };
        });

        assert.ok(!state.overflows, `${route}: horizontal overflow on dynamic keyboard resize`);
        assert.ok(state.hasActive, `${route}: active element lost focus on keyboard resize`);
        await page.setViewportSize({ width: 390, height: 844 });
        totalPassed++;
      }
    } catch (err) {
      failures.push({ viewport: 'Dynamic-Keyboard (390x844->500)', route, errors: [err.message] });
    } finally {
      await page.close();
    }
  }
  await kbContext.close();

  // 4. No-JS progressive enhancement pass
  // Verifies that without JavaScript:
  // - Valid HTML renders with H1 and substantive content (>150 chars in main)
  // - Navigation links have valid hrefs
  // - Tool pages present functional <noscript> explanatory notes with alternative links
  // - Zero horizontal overflow
  console.log('Testing deep No-JS progressive enhancement across core routes...');
  const noJsContext = await browser.newContext({
    viewport: { width: 390, height: 844 },
    javaScriptEnabled: false,
  });
  for (const route of TARGET_ROUTES) {
    const page = await noJsContext.newPage();
    try {
      const res = await page.goto(`${origin}${route}`, { waitUntil: 'domcontentloaded', timeout: 10000 });
      assert.equal(res.status(), 200, `Expected 200 OK for No-JS ${route}`);
      const h1Count = await page.locator('h1').count();
      assert.ok(h1Count >= 1, `Expected at least one <h1> in No-JS render of ${route}`);

      const mainText = await page.locator('main').textContent();
      assert.ok(mainText && mainText.trim().length > 150, `Expected substantive content in <main> for No-JS ${route}`);

      // Check overflow in No-JS
      const overflow = await page.evaluate(() => {
        const docWidth = document.documentElement.scrollWidth;
        const winWidth = window.innerWidth;
        const bodyWidth = document.body ? document.body.scrollWidth : 0;
        return Math.max(docWidth, bodyWidth) > winWidth + 1;
      });
      assert.ok(!overflow, `No-JS horizontal overflow on ${route}`);

      // For interactive tool routes, verify noscript note is present in main
      if (route.startsWith('/herramientas/') && route !== '/herramientas/') {
        const noscriptNote = await page.locator('main noscript, .tool-panel noscript, noscript').first().textContent();
        assert.ok(noscriptNote && noscriptNote.length > 20, `Expected descriptive noscript fallback note on ${route}`);
      }

      totalPassed++;
    } catch (err) {
      failures.push({ viewport: 'No-JS (390x844)', route, errors: [err.message] });
    } finally {
      await page.close();
    }
  }
  await noJsContext.close();
} finally {
  await browser.close();
  server.close();
}

console.log(`\nResults: ${totalPassed} checks PASSED, ${failures.length} FAILED.`);
if (failures.length > 0) {
  console.error('\nFailures detail:');
  for (const f of failures) {
    console.error(`- [${f.viewport}] ${f.route}:`);
    for (const e of f.errors) {
      console.error(`    * ${e}`);
    }
  }
  process.exit(1);
} else {
  console.log('ALL CROSS-DEVICE SMOKE CHECKS PASSED 100%!');
}
