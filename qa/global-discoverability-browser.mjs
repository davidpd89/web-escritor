import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ROOT = process.cwd();
const OUT = process.env.GLOBAL_QA_OUT || path.join(ROOT, 'artifacts', 'global-discoverability');
fs.mkdirSync(OUT, { recursive: true });

const MIME = new Map([
  ['.html', 'text/html; charset=utf-8'], ['.css', 'text/css; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'], ['.mjs', 'text/javascript; charset=utf-8'],
  ['.json', 'application/json; charset=utf-8'], ['.xml', 'application/xml; charset=utf-8'],
  ['.txt', 'text/plain; charset=utf-8'], ['.webp', 'image/webp'], ['.png', 'image/png'],
  ['.jpg', 'image/jpeg'], ['.jpeg', 'image/jpeg'], ['.svg', 'image/svg+xml'],
  ['.woff2', 'font/woff2'], ['.ico', 'image/x-icon'],
]);

function resolvePath(pathname) {
  const clean = decodeURIComponent(pathname.split('?')[0]).replace(/^\/+/, '');
  if (!clean) return path.join(ROOT, 'index.html');
  const candidate = pathname.endsWith('/') ? path.join(ROOT, clean, 'index.html') : path.join(ROOT, clean);
  const normalized = path.resolve(candidate);
  return normalized.startsWith(ROOT) ? normalized : null;
}

const page404 = fs.readFileSync(path.join(ROOT, '404.html'));
const server = createServer((req, res) => {
  const url = new URL(req.url, 'http://127.0.0.1');
  const file = resolvePath(url.pathname);
  if (!file || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
    res.writeHead(404, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' });
    res.end(page404);
    return;
  }
  const type = MIME.get(path.extname(file).toLowerCase()) || 'application/octet-stream';
  res.writeHead(200, { 'Content-Type': type, 'Cache-Control': 'no-store' });
  res.end(fs.readFileSync(file));
});
await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const ORIGIN = `http://127.0.0.1:${server.address().port}`;

const representative = [
  '/', '/las-manecillas-del-recuerdo/', '/libros/samuel-entre-mundos/', '/autor.html',
  '/cuaderno/', '/herramientas/', '/recomendaciones/', '/editoriales/',
  '/convocatorias-escritores/', '/prensa.html', '/eventos.html', '/ferias.html',
  '/privacidad.html', '/mapa-del-sitio/', '/ai/',
];
const viewports = [
  { name: '320x900', width: 320, height: 900 },
  { name: '390x900', width: 390, height: 900 },
  { name: '768x1000', width: 768, height: 1000 },
  { name: '1024x900', width: 1024, height: 900 },
  { name: '1440x1000', width: 1440, height: 1000 },
  { name: '1728x1000', width: 1728, height: 1000 },
  { name: '844x390', width: 844, height: 390 },
];
const report = { origin: ORIGIN, representative: {}, viewports: {}, contracts: {}, noJs: {} };
const browser = await chromium.launch({
  headless: true,
  ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH
    ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH }
    : {}),
});

async function open(page, route) {
  const pageErrors = [];
  const consoleErrors = [];
  page.on('pageerror', (error) => pageErrors.push(error.message));
  page.on('console', (message) => {
    if (message.type() !== 'error') return;
    const text = message.text();
    if (!/(Failed to load resource|ERR_BLOCKED_BY_CLIENT|net::ERR_)/i.test(text)) consoleErrors.push(text);
  });
  const response = await page.goto(`${ORIGIN}${route}`, { waitUntil: 'load' });
  assert(response && response.status() < 400, `${route}: HTTP ${response?.status()}`);
  await page.waitForTimeout(180);
  assert.equal(await page.locator('main').count(), 1, `${route}: main missing`);
  assert.equal(await page.locator('header.site-header').count(), 1, `${route}: V1 header missing`);
  assert.equal(await page.locator('footer.site-footer').count(), 1, `${route}: V1 footer missing`);
  assert.equal(await page.locator('.skip-link').count(), 1, `${route}: skip link missing`);
  const dimensions = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }));
  assert(dimensions.sw <= dimensions.cw + 1, `${route}: horizontal overflow ${dimensions.sw}/${dimensions.cw}`);
  assert.deepEqual(pageErrors, [], `${route}: pageerror ${pageErrors.join(' | ')}`);
  assert.deepEqual(consoleErrors, [], `${route}: console ${consoleErrors.join(' | ')}`);
  return dimensions;
}

try {
  for (const vp of [{ name: '390x900', width: 390, height: 900 }, { name: '1440x1000', width: 1440, height: 1000 }]) {
    report.representative[vp.name] = {};
    for (const route of representative) {
      const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, reducedMotion: 'reduce' });
      const page = await context.newPage();
      await open(page, route);
      report.representative[vp.name][route] = true;
      await context.close();
    }
  }

  for (const vp of viewports) {
    const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    report.viewports[vp.name] = {};
    for (const route of ['/', '/mapa-del-sitio/', '/404.html']) {
      await open(page, route);
      report.viewports[vp.name][route] = true;
    }
    await context.close();
  }

  {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    const page = await context.newPage();
    await open(page, '/');
    const before = await page.locator('.site-header').evaluate((el) => ({ top: el.getBoundingClientRect().top, position: getComputedStyle(el).position }));
    await page.evaluate(() => window.scrollTo(0, Math.min(1200, document.documentElement.scrollHeight - innerHeight)));
    await page.waitForTimeout(120);
    const after = await page.locator('.site-header').evaluate((el) => ({ top: el.getBoundingClientRect().top, position: getComputedStyle(el).position, scrolled: el.dataset.scrolled }));
    assert.equal(before.position, 'sticky', 'header computed position is not sticky');
    assert.equal(after.position, 'sticky', 'header loses sticky after scrolling');
    assert(Math.abs(after.top) <= 1, `sticky header moved away from viewport top: ${after.top}`);
    report.contracts.sticky = { before, after };
    await context.close();
  }

  for (const vp of [{ name: 'mobile', width: 390, height: 900 }, { name: 'desktop', width: 1440, height: 1000 }]) {
    const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, hasTouch: vp.name === 'mobile' });
    const page = await context.newPage();
    await open(page, '/');
    const trigger = page.locator('[data-explore-open]');
    await trigger.focus();
    await trigger.click();
    const dialog = page.locator('[data-explore-dialog]');
    assert.equal(await dialog.evaluate((el) => el.open), true, `Explore ${vp.name}: dialog not open`);
    assert.equal(await trigger.getAttribute('aria-expanded'), 'true', `Explore ${vp.name}: aria-expanded`);
    assert(await page.locator('.explore-row').count() >= 7, `Explore ${vp.name}: expected six canonical rows plus assistant enhancement`);
    for (let i = 0; i < 8; i++) {
      await page.keyboard.press('Tab');
      const inside = await page.evaluate(() => {
        const dialogNode = document.querySelector('[data-explore-dialog]');
        return Boolean(dialogNode && (dialogNode === document.activeElement || dialogNode.contains(document.activeElement)));
      });
      assert(inside, `Explore ${vp.name}: modal focus escaped on Tab ${i + 1}`);
    }
    await page.keyboard.press('Escape');
    await page.waitForTimeout(40);
    assert.equal(await dialog.evaluate((el) => el.open), false, `Explore ${vp.name}: Escape did not close`);
    assert.equal(await page.evaluate(() => document.activeElement?.hasAttribute('data-explore-open')), true, `Explore ${vp.name}: focus did not return to trigger`);
    report.contracts[`explore-${vp.name}`] = true;
    await context.close();
  }

  {
    const context = await browser.newContext({ viewport: { width: 390, height: 900 }, hasTouch: true });
    const page = await context.newPage();
    await open(page, '/');
    await page.locator('[data-explore-open]').click();
    await page.locator('.explore-row[href="/autor.html"]').click();
    await page.waitForLoadState('load');
    assert.equal(new URL(page.url()).pathname, '/autor.html', 'Explore mobile: one tap did not navigate');
    report.contracts.singleTap = true;
    await context.close();
  }

  {
    const context = await browser.newContext({ viewport: { width: 390, height: 900 } });
    const page = await context.newPage();
    const response = await page.goto(`${ORIGIN}/__global_discoverability_missing__/deep/path`, { waitUntil: 'load' });
    assert.equal(response.status(), 404, 'unknown route did not return HTTP 404 in QA edge');
    assert(await page.locator('h1').innerText().then((text) => /no existe/i.test(text)), 'authored 404 rescue page not served');
    for (const href of ['/', '/libros/', '/cuaderno/', '/herramientas/', '/mapa-del-sitio/']) {
      assert(await page.locator(`a[href="${href}"]`).count() > 0, `404 rescue missing ${href}`);
    }
    report.contracts.http404 = true;
    await context.close();
  }

  for (const route of ['/', '/mapa-del-sitio/', '/privacidad.html', '/autor.html', '/herramientas/', '/404.html']) {
    const context = await browser.newContext({ viewport: { width: 390, height: 900 }, javaScriptEnabled: false });
    const page = await context.newPage();
    const response = await page.goto(`${ORIGIN}${route}`, { waitUntil: 'load' });
    assert(response.status() < 400, `${route} no-JS HTTP ${response.status()}`);
    assert(await page.locator('main').isVisible(), `${route}: main unavailable without JS`);
    assert(await page.locator('.primary-nav a').count() >= 3, `${route}: primary navigation unavailable without JS`);
    assert(await page.locator('.site-footer a').count() >= 5, `${route}: footer recovery unavailable without JS`);
    report.noJs[route] = true;
    await context.close();
  }

  async function applyInspectorStyles(ctx, pg, cssText) {
    const cdp = await ctx.newCDPSession(pg);
    await cdp.send('Page.enable');
    await cdp.send('DOM.enable');
    await cdp.send('CSS.enable');
    const { frameTree } = await cdp.send('Page.getFrameTree');
    const { styleSheetId } = await cdp.send('CSS.createStyleSheet', { frameId: frameTree.frame.id });
    await cdp.send('CSS.setStyleSheetText', { styleSheetId, text: cssText });
  }

  for (const route of ['/', '/mapa-del-sitio/']) {
    const context = await browser.newContext({ viewport: { width: 320, height: 900 }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    await open(page, route);
    // addStyleTag inyecta una hoja inline y estas paginas llevan style-src 'self':
    // el navegador la rechaza y la suite muere en /mapa-del-sitio/ antes de medir.
    // Se inyecta como hoja de inspector por CDP, que no pasa por la CSP de la
    // pagina. Es el mismo helper que ya usa qa/pro-resources-browser.mjs.
    await applyInspectorStyles(context, page, '*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}');
    await page.evaluate(() => { document.documentElement.style.fontSize = '200%'; });
    await page.waitForTimeout(80);
    const dimensions = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }));
    assert(dimensions.sw <= dimensions.cw + 1, `${route}: overflow under 200% + text spacing ${dimensions.sw}/${dimensions.cw}`);
    report.contracts[`reflow-${route}`] = true;
    await context.close();
  }

  for (const shot of [
    { route: '/', name: 'home-1440.png', width: 1440, height: 1000 },
    { route: '/mapa-del-sitio/', name: 'map-1440.png', width: 1440, height: 1000 },
    { route: '/mapa-del-sitio/', name: 'map-390.png', width: 390, height: 900 },
    { route: '/404.html', name: '404-390.png', width: 390, height: 900 },
  ]) {
    const context = await browser.newContext({ viewport: { width: shot.width, height: shot.height } });
    const page = await context.newPage();
    await page.goto(`${ORIGIN}${shot.route}`, { waitUntil: 'load' });
    await page.screenshot({ path: path.join(OUT, shot.name), fullPage: false });
    await context.close();
  }

  fs.writeFileSync(path.join(OUT, 'browser-report.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(`PASS: global shell/discoverability browser QA (${representative.length} representative routes)`);
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
