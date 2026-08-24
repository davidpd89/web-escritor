import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

// Run from repository root with a local static server on port 4173.
// Covers the LRB-style masthead nav (PR95, 2026-08-24): a horizontal row of
// territories under the centered masthead logo, each with a chevron trigger
// that discloses a dropdown of direct routes. Desktop reveal is hover/focus
// via plain CSS (no JS needed to see it); the trigger button additionally
// lets touch/keyboard toggle it explicitly and is JS-driven. At <=639px the
// whole row is hidden -- the hamburger/Explore drawer owns global nav there.
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
  page.on('console', msg => {
    if (msg.type() !== 'error') return;
    const text = msg.text();
    // The Home v3 banners probe a canonical asset path first and fall back
    // to an existing image on 404 (assets/v1-home-editorial-v3.js
    // loadFirstImage()) -- expected noise while final banner art is pending,
    // same filter qa/global-discoverability-browser.mjs already applies.
    if (/(Failed to load resource|ERR_BLOCKED_BY_CLIENT|net::ERR_)/i.test(text)) return;
    state.consoleErrors.push(text);
  });
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

async function submenuVisible(page, key) {
  return page.locator(`#masthead-submenu-${key}`).evaluate(el => {
    const cs = getComputedStyle(el);
    return cs.visibility !== 'hidden' && Number(cs.opacity) > 0;
  });
}

async function assertNavVisible(page, label) {
  assert.equal(await page.locator('.masthead-nav__list a[data-territory]').count(), 5, `${label}: cinco territorios`);
  for (const [key, href] of TERRITORIES) {
    const link = page.locator(`[data-territory="${key}"]`);
    assert.equal(await link.getAttribute('href'), href, `${label}: href ${key}`);
    assert.ok(await link.isVisible(), `${label}: ${key} visible`);
  }
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert.ok(overflow <= 1, `${label}: overflow horizontal ${overflow}px`);
}

// Desktop: hover + focus reveal the matching submenu dropdown (pure CSS); the
// chevron trigger also toggles it explicitly via click, with aria-expanded
// kept in sync; Escape closes and returns focus to the trigger.
{
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const { page, errors } = await open(context);
  await assertNavVisible(page, '1440');
  await page.locator('.masthead-nav').scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(OUT, '1440-rest.png') });
  for (const [key] of TERRITORIES) assert.equal(await submenuVisible(page, key), false, `1440 reposo: submenu ${key} oculto`);

  // Keyboard traversal runs first, before anything parks the real mouse
  // pointer over a trigger -- a lingering :hover would keep that submenu
  // open and let Tab walk straight into its links, skipping its own anchor.
  await page.evaluate(() => document.activeElement?.blur());
  const seen = [];
  for (let i = 0; i < 60 && seen.length < 5; i++) {
    await page.keyboard.press('Tab');
    await page.waitForTimeout(30);
    const key = await page.evaluate(() => document.activeElement?.getAttribute?.('data-territory') || '');
    if (key && !seen.includes(key)) {
      seen.push(key);
      assert.equal(await submenuVisible(page, key), true, `focus ${key}: submenu visible`);
    }
  }
  assert.deepEqual(new Set(seen), new Set(TERRITORIES.map(([key]) => key)), '1440: Tab alcanza los cinco territorios');
  await page.evaluate(() => document.activeElement?.blur());

  for (const [key] of TERRITORIES) {
    await page.locator(`[data-territory="${key}"]`).hover();
    await page.waitForTimeout(120);
    assert.equal(await submenuVisible(page, key), true, `hover ${key}: submenu visible`);
    for (const [other] of TERRITORIES) {
      if (other === key) continue;
      assert.equal(await submenuVisible(page, other), false, `hover ${key}: submenu ${other} sigue oculto`);
    }
    if (key === 'works-hub') {
      const first = page.locator(`#masthead-submenu-${key} a`).first();
      assert.equal(await first.getAttribute('href'), '/libros/', 'works-hub: primer enlace del submenu es el hub');
      await page.screenshot({ path: path.join(OUT, '1440-works-hub-active.png') });
    }
  }
  await page.mouse.move(10, 10);
  await page.waitForTimeout(150);

  // Explicit click-toggle on the trigger button (touch/keyboard path).
  const trigger = page.locator('[aria-controls="masthead-submenu-works-hub"]');
  assert.equal(await trigger.getAttribute('aria-expanded'), 'false', 'trigger: cerrado en reposo');
  await trigger.click();
  await page.waitForTimeout(150);
  assert.equal(await trigger.getAttribute('aria-expanded'), 'true', 'trigger: abierto tras click');
  assert.equal(await submenuVisible(page, 'works-hub'), true, 'trigger click: submenu visible');
  await page.keyboard.press('Escape');
  assert.equal(await trigger.getAttribute('aria-expanded'), 'false', 'trigger: cerrado tras Escape');
  assert.ok(await trigger.evaluate(el => el === document.activeElement), 'Escape: foco vuelve al trigger');

  assert.ok((await page.evaluate(() => window.__homeMastheadCls || 0)) <= .1, '1440: CLS <= 0.1');
  assert.deepEqual(errors.pageErrors, [], `1440 pageerror: ${errors.pageErrors.join(' | ')}`);
  assert.deepEqual(errors.consoleErrors, [], `1440 console: ${errors.consoleErrors.join(' | ')}`);
  await context.close();
}

// 1024, 768: nav stays a visible, usable list with working submenus.
for (const [width, height] of [[1024, 900], [768, 1000]]) {
  const context = await browser.newContext({ viewport: { width, height } });
  const { page, errors } = await open(context);
  await assertNavVisible(page, String(width));
  await page.locator('.masthead-nav').scrollIntoViewIfNeeded();
  await page.locator('[data-territory="works-hub"]').hover();
  await page.waitForTimeout(120);
  assert.equal(await submenuVisible(page, 'works-hub'), true, `${width}: hover revela submenu`);
  assert.ok((await page.evaluate(() => window.__homeMastheadCls || 0)) <= .1, `${width}: CLS <= 0.1`);
  assert.deepEqual(errors.pageErrors, [], `${width}: pageerror`);
  assert.deepEqual(errors.consoleErrors, [], `${width}: console error`);
  await context.close();
}

// 390, 320: the territory row hands off entirely to the hamburger/Explore
// drawer -- there is no room for a five-item row plus dropdowns on a phone.
for (const [width, height] of [[390, 900], [320, 900]]) {
  const context = await browser.newContext({ viewport: { width, height } });
  const { page, errors } = await open(context);
  assert.equal(await page.locator('.masthead-nav').evaluate(el => getComputedStyle(el).display), 'none', `${width}: masthead-nav oculto`);
  const explore = page.locator('[data-explore-open]').first();
  assert.ok(await explore.isVisible(), `${width}: hamburger/Explore visible`);
  const box = await explore.boundingBox();
  assert.ok(box && box.height >= 44 && box.width >= 44, `${width}: hamburger target >= 44px`);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert.ok(overflow <= 1, `${width}: overflow horizontal ${overflow}px`);
  assert.ok((await page.evaluate(() => window.__homeMastheadCls || 0)) <= .1, `${width}: CLS <= 0.1`);
  assert.deepEqual(errors.pageErrors, [], `${width}: pageerror`);
  assert.deepEqual(errors.consoleErrors, [], `${width}: console error`);
  if (width === 390) await page.screenshot({ path: path.join(OUT, '390-mobile.png') });
  await context.close();
}

// No-JS: el despliegue por hover es CSS puro (:hover/:focus-within sobre
// .masthead-nav__item), asi que sigue funcionando sin JavaScript -- solo el
// boton de disclosure explicito (click/Escape) depende de v1-shell.js.
{
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, javaScriptEnabled: false });
  const { page, errors } = await open(context);
  await assertNavVisible(page, 'no-js');
  await page.locator('[data-territory="works-hub"]').hover();
  await page.waitForTimeout(120);
  assert.equal(await submenuVisible(page, 'works-hub'), true, 'no-js: submenu via :hover sigue activo');
  assert.deepEqual(errors.pageErrors, [], 'no-js: pageerror');
  assert.deepEqual(errors.consoleErrors, [], 'no-js: console error');
  await context.close();
}

await browser.close();
console.log('HOME MASTHEAD NAV QA PASS');
