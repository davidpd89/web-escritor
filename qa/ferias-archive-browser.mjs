import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const BASE = process.env.FERIAS_BASE_URL || 'http://127.0.0.1:4173';
const OUT = process.env.FERIAS_ARTIFACT_DIR || 'artifacts/ferias-archive';
const viewports = [
  { name: '320x900', width: 320, height: 900 },
  { name: '390x900', width: 390, height: 900 },
  { name: '768x1000', width: 768, height: 1000 },
  { name: '1024x900', width: 1024, height: 900 },
  { name: '1440x900', width: 1440, height: 900 },
];
const events = [
  { id: 'feria-libro-aranjuez-2026', alias: 'aranjuez', shot: 'aranjuez' },
  { id: 'feria-libro-madrid-2026', alias: 'madrid', shot: 'madrid' },
];

const failures = [];
function check(value, message) { if (!value) failures.push(message); }

await fs.mkdir(OUT, { recursive: true });
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

async function contextFor(width, height, extra = {}) {
  return browser.newContext({ viewport: { width, height }, reducedMotion: 'reduce', ...extra });
}

async function openChecked(context, suffix = '') {
  const page = await context.newPage();
  const errors = [];
  const brokenLocal = [];
  page.on('pageerror', (error) => errors.push(`pageerror: ${error.message}`));
  page.on('console', (message) => { if (message.type() === 'error') errors.push(`console: ${message.text()}`); });
  page.on('response', (response) => {
    const url = new URL(response.url());
    if (url.origin === new URL(BASE).origin && response.status() >= 400) brokenLocal.push(`${response.status()} ${url.pathname}`);
  });
  const response = await page.goto(`${BASE}/ferias.html${suffix}`, { waitUntil: 'load' });
  check(response?.ok(), `ferias${suffix}: HTTP ${response?.status() ?? 'no response'}`);
  await page.waitForTimeout(250);
  return { page, errors, brokenLocal };
}

for (const viewport of viewports) {
  const context = await contextFor(viewport.width, viewport.height);
  const { page, errors, brokenLocal } = await openChecked(context);

  // Trigger every native lazy image deterministically before checking natural
  // dimensions. The response listener remains active, so missing assets fail.
  for (const image of await page.locator('img').all()) {
    await image.scrollIntoViewIfNeeded();
  }
  await page.waitForTimeout(150);

  const state = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    canonical: document.querySelector('link[rel="canonical"]')?.href,
    aranjuez: Boolean(document.querySelector('#feria-libro-aranjuez-2026')),
    madrid: Boolean(document.querySelector('#feria-libro-madrid-2026')),
    aliases: Boolean(document.querySelector('#aranjuez')) && Boolean(document.querySelector('#madrid')),
    agenda: [...document.querySelectorAll('a[href="/eventos.html"]')].some((a) => a.textContent.includes('Ver agenda completa')),
    images: [...document.images].map((img) => ({ complete: img.complete, nw: img.naturalWidth, src: img.getAttribute('src') })),
  }));
  check(state.scrollWidth <= state.clientWidth + 1, `${viewport.name}: horizontal overflow ${state.scrollWidth}/${state.clientWidth}`);
  check(state.canonical === 'https://davidportodiaz.com/ferias.html', `${viewport.name}: canonical drift`);
  check(state.aranjuez && state.madrid && state.aliases, `${viewport.name}: archive anchors missing`);
  check(state.agenda, `${viewport.name}: agenda exit missing`);
  check(state.images.every((img) => img.complete && img.nw > 0), `${viewport.name}: one or more local images failed to load`);
  check(errors.length === 0, `${viewport.name}: ${errors.join(' | ')}`);
  check(brokenLocal.length === 0, `${viewport.name}: broken local responses ${[...new Set(brokenLocal)].join(', ')}`);
  await context.close();
}

// Clean visual evidence: canonical deep-link viewport, not a stitched locator
// screenshot. This avoids sticky-shell artefacts while preserving the real UI.
for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 900 }]) {
  for (const event of events) {
    const context = await contextFor(viewport.width, viewport.height);
    const { page, errors, brokenLocal } = await openChecked(context, `#${event.id}`);
    await page.evaluate(() => document.activeElement instanceof HTMLElement && document.activeElement.blur());
    await page.waitForTimeout(100);
    const baseline = await page.locator('.skip-link').evaluate((el) => {
      const rect = el.getBoundingClientRect();
      return { bottom: rect.bottom, transform: getComputedStyle(el).transform };
    });
    check(baseline.bottom <= 0, `screenshot ${event.shot} ${viewport.width}: skip link unexpectedly visible at baseline`);
    check(errors.length === 0, `screenshot ${event.shot} ${viewport.width}: ${errors.join(' | ')}`);
    check(brokenLocal.length === 0, `screenshot ${event.shot} ${viewport.width}: broken local responses ${[...new Set(brokenLocal)].join(', ')}`);
    await page.screenshot({ path: path.join(OUT, `${event.shot}-${viewport.width}x${viewport.height}.png`), fullPage: false });
    await context.close();
  }
}

// Canonical and legacy deep links must land on the corresponding record without being hidden by the sticky shell.
for (const event of events) {
  for (const fragment of [event.id, event.alias]) {
    const context = await contextFor(390, 900);
    const { page, errors } = await openChecked(context, `#${fragment}`);
    const target = await page.locator(`#${fragment}`).evaluate((el) => {
      const rect = el.getBoundingClientRect();
      return { top: rect.top, height: rect.height, hash: location.hash };
    });
    check(target.hash === `#${fragment}`, `deep link #${fragment}: hash changed`);
    check(target.top >= -1 && target.top < 260, `deep link #${fragment}: target not positioned near viewport top (${target.top})`);
    check(errors.length === 0, `deep link #${fragment}: ${errors.join(' | ')}`);
    await context.close();
  }
}

// Keyboard path: skip link must be the first focus target and visibly exposed.
{
  const context = await contextFor(390, 900);
  const { page } = await openChecked(context);
  await page.keyboard.press('Tab');
  await page.waitForTimeout(50);
  const focus = await page.evaluate(() => {
    const el = document.activeElement;
    const rect = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    return {
      text: el.textContent.trim(),
      top: rect.top,
      width: rect.width,
      height: rect.height,
      visibility: style.visibility,
      display: style.display,
      transform: style.transform,
    };
  });
  check(focus.text === 'Saltar al contenido', `keyboard: first focus is not skip link (${focus.text})`);
  check(focus.width > 0 && focus.height > 0 && focus.top >= 0 && focus.visibility !== 'hidden' && focus.display !== 'none', `keyboard: focused skip link is not visible (top ${focus.top}, transform ${focus.transform})`);
  await page.keyboard.press('Enter');
  check((await page.evaluate(() => location.hash)) === '#contenido', 'keyboard: skip link does not navigate to main content');
  await context.close();
}

// 200% reflow equivalent: a 1440px display exposes roughly a 720 CSS-pixel layout viewport.
{
  const context = await contextFor(720, 450);
  const { page, errors } = await openChecked(context);
  const state = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }));
  check(state.sw <= state.cw + 1, `200% reflow equivalent: horizontal overflow ${state.sw}/${state.cw}`);
  check(errors.length === 0, `200% reflow equivalent: ${errors.join(' | ')}`);
  await context.close();
}

// WCAG text-spacing pressure must not introduce horizontal scrolling or clipped records.
{
  const context = await contextFor(390, 900);
  const { page } = await openChecked(context);
  await page.addStyleTag({ content: `
    * { line-height: 1.5 !important; letter-spacing: .12em !important; word-spacing: .16em !important; }
    p, li, dd, figcaption { margin-bottom: 2em !important; }
  ` });
  const state = await page.evaluate(() => ({
    sw: document.documentElement.scrollWidth,
    cw: document.documentElement.clientWidth,
    a: document.querySelector('#feria-libro-aranjuez-2026')?.getBoundingClientRect().height || 0,
    m: document.querySelector('#feria-libro-madrid-2026')?.getBoundingClientRect().height || 0,
  }));
  check(state.sw <= state.cw + 1, `text spacing: horizontal overflow ${state.sw}/${state.cw}`);
  check(state.a > 500 && state.m > 500, 'text spacing: archive records collapsed');
  await context.close();
}

// Public archive must remain complete with JavaScript disabled.
{
  const context = await contextFor(390, 900, { javaScriptEnabled: false });
  const page = await context.newPage();
  const response = await page.goto(`${BASE}/ferias.html#feria-libro-madrid-2026`, { waitUntil: 'load' });
  check(response?.ok(), 'no-JS: HTTP failure');
  const state = await page.evaluate(() => ({
    text: document.querySelector('main')?.innerText || '',
    sw: document.documentElement.scrollWidth,
    cw: document.documentElement.clientWidth,
    chronicle: Boolean(document.querySelector('a[href="/cuaderno/feria-libro-madrid-2026-samuel-entre-mundos/"]')),
    agenda: Boolean(document.querySelector('a[href="/eventos.html"]')),
  }));
  check(state.text.includes('Feria del Libro de Aranjuez 2026') && state.text.includes('Feria del Libro de Madrid 2026'), 'no-JS: archive content missing');
  check(state.chronicle && state.agenda, 'no-JS: essential navigation missing');
  check(state.sw <= state.cw + 1, `no-JS: horizontal overflow ${state.sw}/${state.cw}`);
  await context.close();
}

await browser.close();

if (failures.length) {
  console.error(`ferias browser QA failed (${failures.length})`);
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}
console.log('ferias browser QA: OK');
