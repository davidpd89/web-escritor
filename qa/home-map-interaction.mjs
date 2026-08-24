import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

// Run from repository root with a local static server on port 4173.
// Renamed in spirit (not in filename, to avoid churning the workflow path
// trigger) from the old scattered-map cartography test to the LRB/MUBI-style
// masthead nav that replaced it 2026-08-24: a horizontal row of territories
// under the centered masthead, each revealing an image+copy preview panel
// below on hover/focus via CSS :has() -- no JS drives the reveal.
const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const OUT = path.resolve('qa-artifacts/home-map');
await fs.mkdir(OUT, { recursive: true });

const TERRITORIES = [
  ['works-hub', '/libros/'],
  ['author', '/autor.html'],
  ['notebook-hub', '/cuaderno/'],
  ['tools-hub', '/herramientas/'],
  ['press', '/prensa.html'],
];
const VIEWPORTS = [[1440,900],[1024,900],[768,1000],[390,900],[320,900]];

const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

function trapErrors(page) {
  const state = { pageErrors: [], consoleErrors: [] };
  page.on('pageerror', error => state.pageErrors.push(String(error)));
  page.on('console', msg => { if (msg.type() === 'error') state.consoleErrors.push(msg.text()); });
  return state;
}

async function open(context) {
  const page = await context.newPage();
  const errors = trapErrors(page);
  // El widget del asistente muestra un aviso una vez por sesión. Este suite
  // mide el masthead-nav y no el widget, así que se marca su clave de sesión
  // para evitar superposición accidental durante hover/focus.
  await page.addInitScript(() => {
    try { sessionStorage.setItem('davidporto-assistant-widget-hint-v2', '1'); } catch { /* sin sessionStorage tampoco aparece el aviso */ }
    window.__homeMastheadCls = 0;
    new PerformanceObserver(list => {
      for (const entry of list.getEntries()) if (!entry.hadRecentInput) window.__homeMastheadCls += entry.value;
    }).observe({ type: 'layout-shift', buffered: true });
  });
  await page.goto(`${BASE}/`, { waitUntil: 'networkidle' });
  // La Home cubre el masthead-nav con el overlay de intro (video + boton
  // Entrar) hasta que se descarta; sin esto los hover/focus sobre los
  // territorios fallan por "subtree intercepts pointer events".
  const introEnter = page.locator('[data-intro-enter]').first();
  if ((await introEnter.count()) > 0 && (await introEnter.isVisible())) {
    await introEnter.click();
    await page.waitForTimeout(900);
  }
  await page.waitForTimeout(250);
  return { page, errors };
}

async function assertCore(page, label) {
  assert.equal(await page.locator('.masthead-nav__list a[data-territory]').count(), 5, `${label}: cinco territorios`);
  for (const [key, href] of TERRITORIES) {
    const link = page.locator(`[data-territory="${key}"]`);
    assert.equal(await link.getAttribute('href'), href, `${label}: href ${key}`);
    assert.ok(await link.isVisible(), `${label}: ${key} visible`);
  }
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert.ok(overflow <= 1, `${label}: overflow horizontal ${overflow}px`);
}

async function panelVisible(page, key) {
  return page.locator(`[data-preview-panel="${key}"]`).evaluate(el => getComputedStyle(el).display !== 'none');
}

// Desktop: hover + keyboard focus reveal the matching preview panel; no
// other panel is shown at the same time.
{
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const { page, errors } = await open(context);
  await assertCore(page, '1440');
  await page.locator('.masthead-nav').scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(OUT, '1440-rest.png') });
  for (const [key] of TERRITORIES) assert.equal(await panelVisible(page, key), false, `1440 reposo: panel ${key} oculto`);

  for (const [key] of TERRITORIES) {
    await page.locator(`[data-territory="${key}"]`).hover();
    await page.waitForTimeout(120);
    assert.equal(await panelVisible(page, key), true, `hover ${key}: panel visible`);
    for (const [other] of TERRITORIES) {
      if (other === key) continue;
      assert.equal(await panelVisible(page, other), false, `hover ${key}: panel ${other} sigue oculto`);
    }
    if (key === 'works-hub') await page.screenshot({ path: path.join(OUT, '1440-works-hub-active.png') });
  }

  await page.locator('body').focus();
  const seen = [];
  for (let i = 0; i < 40 && seen.length < 5; i++) {
    await page.keyboard.press('Tab');
    const key = await page.evaluate(() => document.activeElement?.getAttribute?.('data-territory') || '');
    if (key && !seen.includes(key)) {
      seen.push(key);
      assert.equal(await panelVisible(page, key), true, `focus ${key}: panel visible`);
    }
  }
  assert.deepEqual(new Set(seen), new Set(TERRITORIES.map(([key]) => key)), '1440: Tab alcanza los cinco territorios');
  assert.ok((await page.evaluate(() => window.__homeMastheadCls || 0)) <= .1, '1440: CLS <= 0.1');
  assert.deepEqual(errors.pageErrors, [], `1440 pageerror: ${errors.pageErrors.join(' | ')}`);
  assert.deepEqual(errors.consoleErrors, [], `1440 console: ${errors.consoleErrors.join(' | ')}`);
  await context.close();
}

// 1024, 768, 390, 320: nav stays a usable list; preview panel is desktop-only
// (<900px stacks the territories as a plain link list, no room for a
// hover-only preview on a touch viewport).
for (const [width, height] of VIEWPORTS.slice(1)) {
  const context = await browser.newContext({ viewport: { width, height } });
  const { page, errors } = await open(context);
  await assertCore(page, String(width));
  await page.locator('.masthead-nav').scrollIntoViewIfNeeded();
  if (width < 900) {
    assert.equal(await page.locator('.masthead-nav__preview').evaluate(el => getComputedStyle(el).display), 'none', `${width}: preview oculta`);
  }
  if (width <= 767) {
    for (const [key] of TERRITORIES) {
      const box = await page.locator(`[data-territory="${key}"]`).boundingBox();
      assert.ok(box && box.height >= 44, `${width}: target ${key} >= 44px`);
    }
  }
  assert.ok((await page.evaluate(() => window.__homeMastheadCls || 0)) <= .1, `${width}: CLS <= 0.1`);
  assert.deepEqual(errors.pageErrors, [], `${width}: pageerror`);
  assert.deepEqual(errors.consoleErrors, [], `${width}: console error`);
  if (width === 390) await page.screenshot({ path: path.join(OUT, '390-mobile.png') });
  await context.close();
}

// No-JS: la revelacion del panel es CSS puro (:has()), asi que sigue
// funcionando sin JavaScript -- a diferencia del viejo mapa, que dependia
// de initMap() para el estado de foco.
{
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, javaScriptEnabled: false });
  const { page, errors } = await open(context);
  await assertCore(page, 'no-js');
  await page.locator('[data-territory="works-hub"]').hover();
  await page.waitForTimeout(120);
  assert.equal(await panelVisible(page, 'works-hub'), true, 'no-js: preview via :has() sigue activo');
  assert.deepEqual(errors.pageErrors, [], 'no-js: pageerror');
  assert.deepEqual(errors.consoleErrors, [], 'no-js: console error');
  await context.close();
}

await browser.close();
console.log('HOME MASTHEAD NAV QA PASS');
