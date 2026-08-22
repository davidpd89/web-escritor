import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { mkdirSync, readFileSync, statSync, existsSync } from 'node:fs';
import { extname, join, normalize, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const ROOT = resolve(fileURLToPath(new URL('..', import.meta.url)));
const OUT = join(ROOT, 'artifacts', 'pwa-offline');
mkdirSync(OUT, { recursive: true });

const swSource = readFileSync(join(ROOT, 'service-worker.js'), 'utf8');
const offlineSource = readFileSync(join(ROOT, 'offline.html'), 'utf8');
const manifest = JSON.parse(readFileSync(join(ROOT, 'manifest.json'), 'utf8'));
let serveUpdatedWorker = false;

const BASE_SHA = 'e9207278747646b76a0f22ebf3703b3e19c0c3db';
const BASELINE_APP_SHELL = [
  '/offline.html',
  '/manifest.json',
  '/assets/logo-david-porto-diaz-escritor-176.webp',
  '/assets/david-porto-favicon.png',
  '/assets/icon-512.png',
  '/assets/icon-512-maskable.png',
  '/assets/david-porto-autor-700.webp',
  '/assets/david-porto-autor-400.webp',
  '/assets/fonts/cg-normal-latin.woff2',
  '/assets/fonts/cg-normal-latin-ext.woff2',
  '/assets/fonts/cg-italic-latin.woff2',
  '/assets/fonts/inter-normal-latin.woff2',
  '/assets/fonts/inter-normal-latin-ext.woff2'
];

function shellFromSource(source) {
  const match = source.match(/const APP_SHELL = \[([\s\S]*?)\];/);
  assert(match, 'APP_SHELL not found');
  return [...match[1].matchAll(/["']([^"']+)["']/g)].map((entry) => entry[1]);
}

function repoPath(urlPath) {
  const clean = decodeURIComponent(urlPath.split('?')[0]).replace(/^\/+/, '');
  if (!clean) return join(ROOT, 'index.html');
  if (clean.endsWith('/')) return join(ROOT, clean, 'index.html');
  return join(ROOT, clean);
}

function fileInfo(urlPath) {
  const path = repoPath(urlPath);
  return { path, exists: existsSync(path), bytes: existsSync(path) ? statSync(path).size : 0 };
}

function pngDimensions(path) {
  const bytes = readFileSync(path);
  assert(bytes.length >= 24, `${path} PNG too short`);
  assert.equal(bytes.subarray(1, 4).toString('ascii'), 'PNG', `${path} is not PNG`);
  return { width: bytes.readUInt32BE(16), height: bytes.readUInt32BE(20) };
}

const appShell = shellFromSource(swSource);
const baseline = BASELINE_APP_SHELL.map((path) => ({ path, ...fileInfo(path) }));
const current = appShell.map((path) => ({ path, ...fileInfo(path) }));
const baselineBytes = baseline.reduce((sum, entry) => sum + entry.bytes, 0);
const currentBytes = current.reduce((sum, entry) => sum + entry.bytes, 0);
const baselineMissing = baseline.filter((entry) => !entry.exists).map((entry) => entry.path);

for (const entry of current) assert(entry.exists, `APP_SHELL path missing: ${entry.path}`);
assert.equal(appShell.filter((path) => path.endsWith('.html')).join(','), '/offline.html', 'Only offline.html may be precached');
for (const legacy of ['cg-normal', 'cg-italic', 'inter-normal', 'david-porto-autor-', 'logo-david-porto-diaz-escritor-176']) {
  assert(!appShell.some((path) => path.includes(legacy)), `Legacy APP_SHELL entry retained: ${legacy}`);
}
assert(appShell.includes('/assets/fonts/is-normal-400-latin.woff2'), 'Instrument Serif V1 fallback not precached');
assert(appShell.includes('/assets/fonts/mr-normal-400-700-latin.woff2'), 'Manrope V1 fallback not precached');
assert(!appShell.some((path) => path.includes('/assets/fonts/nr-')), 'Newsreader should not be cached unless offline.html uses it');
assert(swSource.includes('const CACHE_NAMESPACE = "david-porto-pwa"'), 'PWA cache namespace missing');
assert(swSource.includes('key.startsWith(`${CACHE_NAMESPACE}-`)'), 'activate must restrict cleanup to PWA namespace');
assert(!swSource.includes('.filter((key) => !key.startsWith(CACHE_VERSION))'), 'Broad cache deletion regression');
assert(swSource.includes('await cache.addAll('), 'APP_SHELL installation must be atomic');

assert.equal(manifest.name, 'David Porto Díaz — Escritor');
assert.equal(manifest.short_name, 'David Porto');
assert.equal(manifest.start_url, '/');
assert.equal(manifest.scope, '/');
assert.equal(manifest.display, 'standalone');
assert.equal(manifest.background_color, '#080a0c');
assert.equal(manifest.theme_color, '#080a0c');
assert(Array.isArray(manifest.icons) && manifest.icons.length >= 2, 'Manifest icons missing');
assert(manifest.icons.some((icon) => String(icon.purpose || '').split(/\s+/).includes('maskable')), 'Maskable icon declaration missing');

const iconAudit = manifest.icons.map((icon) => {
  const info = fileInfo(icon.src);
  assert(info.exists, `Manifest icon missing: ${icon.src}`);
  const dimensions = pngDimensions(info.path);
  assert.equal(icon.sizes, `${dimensions.width}x${dimensions.height}`, `Manifest size mismatch: ${icon.src}`);
  return { src: icon.src, purpose: icon.purpose || 'any', ...dimensions, bytes: info.bytes };
});

for (const shortcut of manifest.shortcuts || []) {
  assert(fileInfo(shortcut.url).exists, `Shortcut target missing: ${shortcut.url}`);
}
assert(fileInfo(manifest.start_url).exists, `start_url target missing: ${manifest.start_url}`);

for (const forbidden of ['goatcounter', 'metricool', 'turnstile', 'challenges.cloudflare.com', 'gc.zgo.at', 'tracker.metricool.com']) {
  assert(!offlineSource.toLowerCase().includes(forbidden), `offline.html third-party regression: ${forbidden}`);
}
assert(!/https?:\/\//i.test(offlineSource), 'offline.html must not contain external HTTP(S) URLs');
assert(offlineSource.includes('font-display: swap'), 'Offline fonts must not cause FOIT');
assert(offlineSource.includes('env(safe-area-inset-'), 'Safe-area support missing');
assert(offlineSource.includes('prefers-reduced-motion: reduce'), 'Reduced-motion support missing');
assert(offlineSource.includes('.no-js .actions'), 'No-JS progressive enhancement guard missing');

const MIME = new Map([
  ['.html', 'text/html; charset=utf-8'],
  ['.json', 'application/json; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'],
  ['.mjs', 'text/javascript; charset=utf-8'],
  ['.css', 'text/css; charset=utf-8'],
  ['.png', 'image/png'],
  ['.webp', 'image/webp'],
  ['.ico', 'image/x-icon'],
  ['.woff2', 'font/woff2']
]);

function send(res, status, body, type = 'text/plain; charset=utf-8') {
  res.writeHead(status, { 'Content-Type': type, 'Cache-Control': 'no-store' });
  res.end(body);
}

const server = createServer((req, res) => {
  const url = new URL(req.url, 'http://127.0.0.1');
  if (url.pathname === '/service-worker.js') {
    let body = swSource;
    if (serveUpdatedWorker) {
      body = body.replace(
        'const CACHE_VERSION = `${CACHE_NAMESPACE}-v3`;',
        'const CACHE_VERSION = `${CACHE_NAMESPACE}-v3-qa-update`;'
      );
    }
    return send(res, 200, body, 'text/javascript; charset=utf-8');
  }
  if (url.pathname === '/__pwa_test__/register.html') {
    return send(res, 200, '<!doctype html><html lang="es"><head><link rel="manifest" href="/manifest.json"><title>PWA QA</title></head><body><main><h1>PWA QA</h1></main></body></html>', 'text/html; charset=utf-8');
  }
  if (url.pathname === '/__pwa_test__/recovery-target') {
    return send(res, 200, '<!doctype html><html lang="es"><body><h1>RECOVERY TARGET</h1></body></html>', 'text/html; charset=utf-8');
  }
  if (url.pathname === '/__pwa_test__/not-found') {
    return send(res, 404, '<!doctype html><html><body><h1>EXPECTED 404</h1></body></html>', 'text/html; charset=utf-8');
  }
  if (url.pathname === '/__pwa_test__/server-error') {
    return send(res, 500, '<!doctype html><html><body><h1>EXPECTED 500</h1></body></html>', 'text/html; charset=utf-8');
  }

  const normalized = normalize(url.pathname).replace(/^(\.\.(\/|\\|$))+/, '');
  const path = repoPath(normalized);
  if (!path.startsWith(ROOT) || !existsSync(path)) return send(res, 404, 'Not found');
  const type = MIME.get(extname(path).toLowerCase()) || 'application/octet-stream';
  return send(res, 200, readFileSync(path), type);
});

await new Promise((resolveListen) => server.listen(0, '127.0.0.1', resolveListen));
const port = server.address().port;
const origin = `http://127.0.0.1:${port}`;
const browser = await chromium.launch({ headless: true });
const report = {
  baseContract: `implementacion-web-2026@${BASE_SHA}`,
  appShell,
  baselineAppShell: baseline,
  cacheBytes: {
    beforeExistingBytes: baselineBytes,
    beforeDeclaredEntries: baseline.length,
    beforeMissingEntries: baselineMissing,
    afterBytes: currentBytes,
    afterEntries: current.length
  },
  icons: iconAudit,
  browser: {},
  screenshots: []
};

try {
  const context = await browser.newContext({ viewport: { width: 390, height: 900 }, serviceWorkers: 'allow' });
  const page = await context.newPage();
  const pageErrors = [];
  const consoleErrors = [];
  const externalRequests = [];
  page.on('pageerror', (error) => pageErrors.push(error.message));
  page.on('console', (message) => {
    if (message.type() === 'error' && !message.text().includes('Failed to load resource')) consoleErrors.push(message.text());
  });
  context.on('request', (request) => {
    const requestUrl = new URL(request.url());
    if (requestUrl.origin !== origin) externalRequests.push(request.url());
  });

  const workerPromise = context.waitForEvent('serviceworker');
  await page.goto(`${origin}/__pwa_test__/register.html`, { waitUntil: 'domcontentloaded' });
  const registrationPromise = page.evaluate(async () => {
    const reg = await navigator.serviceWorker.register('/service-worker.js');
    await navigator.serviceWorker.ready;
    if (!navigator.serviceWorker.controller) {
      await new Promise((resolveController) => {
        const timer = setTimeout(resolveController, 5000);
        navigator.serviceWorker.addEventListener('controllerchange', () => {
          clearTimeout(timer);
          resolveController();
        }, { once: true });
      });
    }
    return { scope: reg.scope, controlled: Boolean(navigator.serviceWorker.controller), state: reg.active?.state || null };
  });
  const worker = await workerPromise;
  await worker.evaluate(async () => {
    if (self.registration.active?.state === 'activated') return;
    await new Promise((resolveActivated) => {
      const timer = setTimeout(resolveActivated, 5000);
      self.addEventListener('activate', () => {
        clearTimeout(timer);
        resolveActivated();
      }, { once: true });
    });
  }).catch(() => undefined);
  const registration = await registrationPromise;
  assert.equal(registration.scope, `${origin}/`, 'Unexpected service worker scope');
  assert.equal(registration.controlled, true, 'Page is not controlled after service worker activation');
  assert.equal(registration.state, 'activated', 'Service worker is not activated');

  const cdp = await context.newCDPSession(page);
  const chromiumManifest = await cdp.send('Page.getAppManifest');
  assert.equal(chromiumManifest.errors?.length || 0, 0, `Chromium manifest errors: ${JSON.stringify(chromiumManifest.errors)}`);
  let installabilityErrors = [];
  try {
    ({ installabilityErrors = [] } = await cdp.send('Page.getInstallabilityErrors'));
  } catch (error) {
    report.browser.installabilityProbe = `CDP Page.getInstallabilityErrors unavailable: ${error.message}`;
  }
  if (installabilityErrors.length) {
    report.browser.installabilityErrors = installabilityErrors;
    throw new Error(`Chromium installability errors: ${JSON.stringify(installabilityErrors)}`);
  }
  report.browser.installabilityErrors = installabilityErrors;

  for (const path of appShell) {
    const cached = await page.evaluate(async (url) => Boolean(await caches.match(url)), path);
    assert(cached, `APP_SHELL entry not cached after install: ${path}`);
  }

  for (const icon of manifest.icons) {
    const response = await context.request.get(`${origin}${icon.src}`);
    assert.equal(response.status(), 200, `Manifest icon HTTP failure: ${icon.src}`);
  }

  const response404 = await page.goto(`${origin}/__pwa_test__/not-found`, { waitUntil: 'domcontentloaded' });
  assert.equal(response404.status(), 404, 'Online navigation 404 must remain 404');
  assert(await page.locator('text=EXPECTED 404').isVisible(), '404 was replaced by offline fallback');
  const response500 = await page.goto(`${origin}/__pwa_test__/server-error`, { waitUntil: 'domcontentloaded' });
  assert.equal(response500.status(), 500, 'Online navigation 500 must remain 500');
  assert(await page.locator('text=EXPECTED 500').isVisible(), '500 was replaced by offline fallback');

  const recoveryUrl = `${origin}/__pwa_test__/recovery-target?case=online-event`;
  const recoveryPattern = `${origin}/__pwa_test__/recovery-target**`;
  await context.route(recoveryPattern, async (route) => {
    if (route.request().serviceWorker()) {
      await route.abort('internetdisconnected');
    } else {
      await route.continue();
    }
  });
  const externalBeforeFallback = externalRequests.length;
  const fallbackResponse = await page.goto(recoveryUrl, { waitUntil: 'domcontentloaded' });
  assert(fallbackResponse?.fromServiceWorker(), 'Offline fallback navigation was not handled by the service worker');
  assert(await page.locator('#offline-title').isVisible(), 'Offline navigation fallback not rendered');
  assert.equal(page.url(), recoveryUrl, 'Offline fallback changed requested URL');
  assert.equal(externalRequests.slice(externalBeforeFallback).length, 0, 'Offline fallback made external requests');
  await context.unroute(recoveryPattern);

  await page.evaluate(() => {
    sessionStorage.setItem('__pwaQaOnlineEvents', '0');
    window.addEventListener('online', () => {
      const count = Number(sessionStorage.getItem('__pwaQaOnlineEvents') || '0') + 1;
      sessionStorage.setItem('__pwaQaOnlineEvents', String(count));
    });
  });
  await context.setOffline(true);
  assert.equal(await page.evaluate(() => navigator.onLine), false, 'navigator.onLine did not enter offline state');
  await context.setOffline(false);
  await page.waitForSelector('text=RECOVERY TARGET', { timeout: 7000 });
  assert.equal(page.url(), recoveryUrl, 'Online recovery did not preserve requested URL');
  const onlineEventCount = await page.evaluate(() => Number(sessionStorage.getItem('__pwaQaOnlineEvents') || '0'));
  assert.equal(onlineEventCount, 1, 'Online recovery fired more than once / possible reload loop');
  report.browser.recovery = { result: 'network failure -> offline fallback -> online event -> same URL recovered', onlineEventCount };

  const retryUrl = `${origin}/__pwa_test__/recovery-target?case=retry-button`;
  await context.route(recoveryPattern, async (route) => {
    if (route.request().serviceWorker()) await route.abort('internetdisconnected');
    else await route.continue();
  });
  await page.goto(retryUrl, { waitUntil: 'domcontentloaded' });
  assert(await page.locator('#offline-title').isVisible(), 'Retry case did not reach offline fallback');
  await context.unroute(recoveryPattern);
  await page.locator('[data-retry]').click();
  await page.waitForSelector('text=RECOVERY TARGET', { timeout: 5000 });
  assert.equal(page.url(), retryUrl, 'Retry button did not preserve requested URL');
  report.browser.retry = 'PASS';

  const missingAssetPattern = `${origin}/assets/__pwa_qa_missing.*`;
  await context.route(missingAssetPattern, async (route) => {
    if (route.request().serviceWorker()) await route.abort('internetdisconnected');
    else await route.continue();
  });
  for (const assetPath of ['/assets/__pwa_qa_missing.css', '/assets/__pwa_qa_missing.js', '/assets/__pwa_qa_missing.png']) {
    const assetResult = await page.evaluate(async (url) => {
      const response = await fetch(url);
      return { status: response.status, type: response.headers.get('content-type') || '', text: await response.text() };
    }, assetPath);
    assert.equal(assetResult.status, 504, `Offline asset must return 504: ${assetPath}`);
    assert(!assetResult.type.includes('text/html'), `Offline asset received HTML fallback: ${assetPath}`);
    assert.equal(assetResult.text, 'Offline');
  }
  await context.unroute(missingAssetPattern);

  await page.goto(`${origin}/offline.html`, { waitUntil: 'networkidle' });
  await page.keyboard.press('Tab');
  const focusAudit = await page.evaluate(() => {
    const active = document.activeElement;
    const style = getComputedStyle(active);
    return { retryFocused: active?.matches('[data-retry]') || false, outlineStyle: style.outlineStyle, outlineWidth: style.outlineWidth };
  });
  assert.equal(focusAudit.retryFocused, true, 'First keyboard focus should reach Retry');
  assert.notEqual(focusAudit.outlineStyle, 'none', 'focus-visible outline missing');

  const viewports = [
    { width: 320, height: 900 },
    { width: 390, height: 900 },
    { width: 768, height: 1000 },
    { width: 1440, height: 900 }
  ];
  report.browser.viewports = [];
  for (const viewport of viewports) {
    await page.setViewportSize(viewport);
    await page.goto(`${origin}/offline.html`, { waitUntil: 'networkidle' });
    const dimensions = await page.evaluate(() => ({ innerWidth, scrollWidth: document.documentElement.scrollWidth }));
    assert(dimensions.scrollWidth <= dimensions.innerWidth + 1, `Horizontal overflow at ${viewport.width}px`);
    const shot = `offline-${viewport.width}x${viewport.height}.png`;
    await page.screenshot({ path: join(OUT, shot), fullPage: true });
    report.screenshots.push(shot);
    report.browser.viewports.push({ ...viewport, ...dimensions });
  }

  await page.setViewportSize({ width: 320, height: 900 });
  await page.goto(`${origin}/offline.html`, { waitUntil: 'networkidle' });
  await page.addStyleTag({ content: '*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}' });
  const spacing = await page.evaluate(() => ({ innerWidth, scrollWidth: document.documentElement.scrollWidth }));
  assert(spacing.scrollWidth <= spacing.innerWidth + 1, 'WCAG text-spacing stress causes horizontal overflow');
  report.browser.textSpacing = spacing;

  const cdpZoom = await context.newCDPSession(page);
  await cdpZoom.send('Emulation.setPageScaleFactor', { pageScaleFactor: 2 });
  const zoomScale = await page.evaluate(() => window.visualViewport?.scale || 1);
  assert(zoomScale >= 1.9, `Chromium 200% page scale not applied: ${zoomScale}`);
  await cdpZoom.send('Emulation.setPageScaleFactor', { pageScaleFactor: 1 });
  report.browser.zoom200 = zoomScale;

  const noJs = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 320, height: 900 } });
  const noJsPage = await noJs.newPage();
  await noJsPage.goto(`${origin}/offline.html`, { waitUntil: 'domcontentloaded' });
  assert(await noJsPage.locator('#offline-title').isVisible(), 'No-JS offline identity/message missing');
  assert(await noJsPage.locator('.lead').isVisible(), 'No-JS explanation missing');
  assert.equal(await noJsPage.locator('.actions').isVisible(), false, 'No-JS action buttons must not pretend to work');
  await noJs.close();

  const reduced = await browser.newContext({ reducedMotion: 'reduce', viewport: { width: 390, height: 900 } });
  const reducedPage = await reduced.newPage();
  await reducedPage.goto(`${origin}/offline.html`, { waitUntil: 'domcontentloaded' });
  assert.equal(await reducedPage.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches), true);
  await reduced.close();

  await page.goto(`${origin}/__pwa_test__/register.html`, { waitUntil: 'domcontentloaded' });
  await page.evaluate(async () => {
    await caches.open('qa-unrelated-cache');
    await caches.open('david-porto-pwa-v2-test-old');
  });
  serveUpdatedWorker = true;
  const updateAudit = await page.evaluate(async () => {
    const reg = await navigator.serviceWorker.getRegistration('/');
    const changed = new Promise((resolveChanged) => {
      navigator.serviceWorker.addEventListener('controllerchange', resolveChanged, { once: true });
      setTimeout(resolveChanged, 8000);
    });
    await reg.update();
    await changed;
    await new Promise((resolveDelay) => setTimeout(resolveDelay, 300));
    return { caches: await caches.keys(), controlled: Boolean(navigator.serviceWorker.controller) };
  });
  assert(updateAudit.caches.includes('qa-unrelated-cache'), 'Update deleted an unrelated cache');
  assert(!updateAudit.caches.includes('david-porto-pwa-v2-test-old'), 'Update did not clean obsolete namespaced cache');
  assert(!updateAudit.caches.includes('david-porto-pwa-v3-static'), 'Update did not clean previous static cache');
  assert(updateAudit.caches.includes('david-porto-pwa-v3-qa-update-static'), 'Updated static cache missing');
  assert.equal(updateAudit.controlled, true, 'Updated service worker lost page control');
  report.browser.update = updateAudit;

  assert.equal(pageErrors.length, 0, `pageerror: ${pageErrors.join(' | ')}`);
  assert.equal(consoleErrors.length, 0, `console errors: ${consoleErrors.join(' | ')}`);
  report.browser.pageErrors = pageErrors;
  report.browser.consoleErrors = consoleErrors;
  report.browser.externalRequests = externalRequests;
  await context.close();
} finally {
  await browser.close();
  await new Promise((resolveClose) => server.close(resolveClose));
}

const reportPath = join(OUT, 'report.json');
await import('node:fs/promises').then(({ writeFile }) => writeFile(reportPath, `${JSON.stringify(report, null, 2)}\n`));
console.log(JSON.stringify({
  status: 'PASS',
  appShellEntries: appShell.length,
  cacheBytesBeforeExisting: baselineBytes,
  cacheBytesAfter: currentBytes,
  missingBaseline: baselineMissing,
  icons: iconAudit,
  installabilityErrors: report.browser.installabilityErrors,
  screenshots: report.screenshots
}, null, 2));
