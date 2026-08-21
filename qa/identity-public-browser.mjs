import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const BASE = process.env.IDENTITY_BASE_URL || 'http://127.0.0.1:4173';
const OUT = process.env.IDENTITY_ARTIFACT_DIR || 'artifacts/identity-public';
const routes = ['/autor.html', '/prensa.html', '/premios.html', '/eventos.html'];
const viewports = [
  { name: '320', width: 320, height: 780 },
  { name: '390', width: 390, height: 844 },
  { name: '768', width: 768, height: 1024 },
  { name: '1024', width: 1024, height: 900 },
  { name: '1440', width: 1440, height: 1000 },
  { name: '1728', width: 1728, height: 1050 },
  { name: 'landscape-844x390', width: 844, height: 390 },
];

const failures = [];
const metrics = [];
function fail(message) { failures.push(message); }
function check(value, message) { if (!value) fail(message); }

await fs.mkdir(OUT, { recursive: true });
const browser = await chromium.launch({ headless: true });

async function newContext(viewport, extra = {}) {
  return browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
    reducedMotion: 'reduce',
    ...extra,
  });
}

async function openChecked(context, route) {
  const page = await context.newPage();
  const errors = [];
  const brokenLocal = [];
  await page.addInitScript(() => {
    window.__identityCLS = 0;
    try {
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (!entry.hadRecentInput) window.__identityCLS += entry.value;
        }
      }).observe({ type: 'layout-shift', buffered: true });
    } catch (_) {}
  });
  page.on('pageerror', (error) => errors.push(`pageerror: ${error.message}`));
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(`console: ${message.text()}`);
  });
  page.on('response', (response) => {
    const url = new URL(response.url());
    if (url.origin === new URL(BASE).origin && response.status() >= 400) {
      brokenLocal.push(`${response.status()} ${url.pathname}`);
    }
  });
  const response = await page.goto(BASE + route, { waitUntil: 'load' });
  check(response && response.ok(), `${route}: HTTP ${response?.status() ?? 'no response'}`);
  await page.waitForTimeout(350);
  const layout = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    cls: window.__identityCLS || 0,
    title: document.title,
    mainText: document.querySelector('main')?.innerText.trim().length || 0,
  }));
  return { page, errors, brokenLocal, layout };
}

// Cross-route runtime and reflow at all required artboards.
for (const viewport of viewports) {
  for (const route of routes) {
    const context = await newContext(viewport);
    const { page, errors, brokenLocal, layout } = await openChecked(context, route);
    check(layout.scrollWidth <= layout.clientWidth + 1, `${route} @ ${viewport.name}: horizontal overflow ${layout.scrollWidth}/${layout.clientWidth}`);
    check(layout.mainText > 200, `${route} @ ${viewport.name}: main content unexpectedly short`);
    check(errors.length === 0, `${route} @ ${viewport.name}: ${errors.join(' | ')}`);
    check(brokenLocal.length === 0, `${route} @ ${viewport.name}: broken local assets ${[...new Set(brokenLocal)].join(', ')}`);
    check(layout.cls <= 0.1, `${route} @ ${viewport.name}: CLS ${layout.cls.toFixed(4)} > 0.1`);
    metrics.push({ route, viewport: viewport.name, cls: layout.cls, overflow: layout.scrollWidth - layout.clientWidth });
    await context.close();
  }
}

// Autor: portrait is a real img with intrinsic dimensions and remains visible.
{
  const context = await newContext({ width: 390, height: 844 });
  const { page } = await openChecked(context, '/autor.html');
  const portrait = page.locator('.author-portrait img');
  check(await portrait.count() === 1, 'autor: expected one main portrait');
  const p = await portrait.evaluate((img) => ({
    w: img.getBoundingClientRect().width,
    h: img.getBoundingClientRect().height,
    nw: img.naturalWidth,
    nh: img.naturalHeight,
    width: img.getAttribute('width'),
    height: img.getAttribute('height'),
    fetchpriority: img.getAttribute('fetchpriority'),
    loading: img.getAttribute('loading'),
  }));
  check(p.w > 250 && p.h > 300 && p.nw > 0, 'autor: portrait not visibly loaded on mobile');
  check(Boolean(p.width && p.height), 'autor: portrait lacks intrinsic dimensions');
  check(p.fetchpriority === 'high', 'autor: portrait lost fetchpriority=high');
  check(p.loading !== 'lazy', 'autor: LCP candidate must not be lazy');
  await context.close();
}

// Prensa: mobile fact sheets must stack; copy controls, fallback and print work.
{
  const context = await newContext({ width: 390, height: 844 });
  await context.addInitScript(() => {
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText: async (text) => { window.__copiedText = text; } },
    });
  });
  const { page } = await openChecked(context, '/prensa.html');

  const factSheets = await page.locator('#ficha-manecillas > div[style*="grid-template-columns"], #ficha > div[style*="grid-template-columns"]').evaluateAll((nodes) => nodes.map((node) => {
    const children = [...node.children].filter((child) => child instanceof HTMLElement);
    const first = children[0]?.getBoundingClientRect();
    const second = children[1]?.getBoundingClientRect();
    return {
      columns: getComputedStyle(node).gridTemplateColumns,
      stacked: Boolean(first && second && second.top >= first.bottom - 1),
    };
  }));
  check(factSheets.length === 2, `prensa: expected two book fact-sheet grids, got ${factSheets.length}`);
  check(factSheets.every((sheet) => !sheet.columns.includes(' ')), `prensa: fact sheets remain multi-column at 390px (${factSheets.map((sheet) => sheet.columns).join(' | ')})`);
  check(factSheets.every((sheet) => sheet.stacked), 'prensa: book facts and cover are not vertically stacked at 390px');

  const buttons = page.locator('.copy-btn');
  check(await buttons.count() >= 4, 'prensa: expected at least four copy controls');
  const first = buttons.first();
  check(await first.getAttribute('aria-live') === 'polite', 'prensa: copy feedback is not aria-live polite');
  const targetId = await first.getAttribute('data-copy-target');
  const expected = (await page.locator(`#${targetId}`).textContent()).trim();
  await first.click();
  await page.waitForFunction(() => document.querySelector('.copy-btn')?.textContent.includes('Copiado'));
  const copied = await page.evaluate(() => window.__copiedText);
  check(copied === expected, 'prensa: copy control did not copy exactly the intended plain text');
  await page.waitForTimeout(2300);
  await first.click();
  await page.waitForFunction(() => document.querySelector('.copy-btn')?.textContent.includes('Copiado'));
  check((await page.evaluate(() => window.__copiedText)) === expected, 'prensa: copy control failed on repeated use');
  await page.screenshot({ path: path.join(OUT, 'prensa-390-copied.png'), fullPage: true });

  await page.emulateMedia({ media: 'print' });
  const printState = await page.evaluate(() => ({
    main: getComputedStyle(document.querySelector('main')).display,
    header: getComputedStyle(document.querySelector('.site-header')).display,
    copy: getComputedStyle(document.querySelector('.copy-btn')).display,
    contact: document.querySelector('#contacto')?.innerText.includes('samuelentremundos@gmail.com') || false,
    facts: (document.querySelector('#ficha-manecillas')?.innerText.includes('979-8-90514-935-1') || false) && (document.querySelector('#ficha')?.innerText.includes('9791387659776') || false),
  }));
  check(printState.main !== 'none', 'prensa print: main content hidden');
  check(printState.header === 'none', 'prensa print: navigation not removed');
  check(printState.copy === 'none', 'prensa print: copy controls not removed');
  check(printState.contact, 'prensa print: contact missing');
  check(printState.facts, 'prensa print: book facts missing');
  await context.close();

  const fallbackContext = await newContext({ width: 390, height: 844 });
  await fallbackContext.addInitScript(() => {
    try { Object.defineProperty(navigator, 'clipboard', { configurable: true, value: undefined }); } catch (_) {}
    Document.prototype.execCommand = function(command) { return command === 'copy'; };
  });
  const fallbackPage = await fallbackContext.newPage();
  await fallbackPage.goto(BASE + '/prensa.html', { waitUntil: 'domcontentloaded' });
  await fallbackPage.locator('.copy-btn').first().click();
  await fallbackPage.waitForFunction(() => document.querySelector('.copy-btn')?.textContent.includes('Copiado'));
  check((await fallbackPage.locator('.copy-btn').first().textContent()).includes('Copiado'), 'prensa: fallback copy path did not report success');
  await fallbackContext.close();
}

// Premios: only true recognitions in award schema; trajectory and reception are separate.
{
  const context = await newContext({ width: 1440, height: 1000 });
  const { page } = await openChecked(context, '/premios.html');
  const result = await page.evaluate(() => {
    const docs = [...document.querySelectorAll('script[type="application/ld+json"]')].map((s) => JSON.parse(s.textContent));
    const nodes = docs.flatMap((d) => d['@graph'] || [d]);
    const person = nodes.find((n) => n['@type'] === 'Person');
    const ledgerGeometry = [...document.querySelectorAll('.awards-ledger li')].map((item) => {
      const label = item.querySelector(':scope > span')?.getBoundingClientRect();
      const title = item.querySelector('h3')?.getBoundingClientRect();
      return label && title ? { labelRight: label.right, titleLeft: title.left } : null;
    }).filter(Boolean);
    return {
      awards: person?.award || [],
      recognition: document.querySelector('#reconocimientos')?.innerText || '',
      trajectory: document.querySelector('#colaboraciones')?.innerText || '',
      reception: document.querySelector('#recepcion')?.innerText || '',
      ledgerGeometry,
    };
  });
  check(result.awards.length === 2, `premios: expected 2 schema awards, got ${result.awards.length}`);
  check(!result.awards.join(' ').toLowerCase().includes('antolog'), 'premios: anthology still appears as schema award');
  check(!result.recognition.includes('Debut novelístico publicado'), 'premios: debut still classified as recognition');
  check(result.trajectory.includes('Debut novelístico publicado'), 'premios: debut missing from trajectory');
  check(result.trajectory.includes('Antología colaborativa'), 'premios: anthology missing from trajectory');
  check(result.reception.includes('Reseñas de lectores'), 'premios: reader reviews missing from reception');
  check(result.ledgerGeometry.every(({ labelRight, titleLeft }) => labelRight <= titleLeft), 'premios: ledger date/result column overlaps a record title at 1440px');
  await context.close();

  const mobileContext = await newContext({ width: 390, height: 844 });
  const { page: mobilePage } = await openChecked(mobileContext, '/premios.html');
  const mobileColumns = await mobilePage.locator('.awards-ledger li').first().evaluate((item) => getComputedStyle(item).gridTemplateColumns);
  check(!mobileColumns.includes(' '), `premios: ledger does not collapse to one column at 390px (${mobileColumns})`);
  await mobileContext.close();
}

// Eventos: upcoming empty state first, only two authorized archive records, both EventCompleted.
{
  const context = await newContext({ width: 1440, height: 1000 });
  const { page } = await openChecked(context, '/eventos.html');
  const state = await page.evaluate(() => {
    const main = document.querySelector('main');
    const docs = [...document.querySelectorAll('script[type="application/ld+json"]')].map((s) => JSON.parse(s.textContent));
    const nodes = docs.flatMap((d) => d['@graph'] || [d]);
    const events = nodes.filter((n) => n['@type'] === 'Event');
    const aranjuez = events.find((e) => String(e['@id']).includes('aranjuez'));
    return {
      upcomingBeforeArchive: main.querySelector('#proximos').compareDocumentPosition(main.querySelector('#pasados')) & Node.DOCUMENT_POSITION_FOLLOWING,
      emptyText: main.querySelector('#proximos')?.innerText || '',
      archiveText: main.querySelector('#pasados')?.innerText || '',
      events,
      aranjuezImage: aranjuez?.image || null,
      aranjuezOrganizerUrl: aranjuez?.organizer?.url || null,
    };
  });
  check(Boolean(state.upcomingBeforeArchive), 'eventos: upcoming state does not precede archive');
  check(state.emptyText.includes('Ahora mismo no hay una próxima fecha publicada.'), 'eventos: useful empty state missing');
  check(state.emptyText.includes('Solicitar presentación'), 'eventos: empty state lacks presentation action');
  check(state.events.length === 2, `eventos: expected 2 Event schemas, got ${state.events.length}`);
  check(state.events.every((e) => e.eventStatus === 'https://schema.org/EventCompleted'), 'eventos: completed status not preserved');
  check(state.aranjuezImage === 'https://davidportodiaz.com/assets/feria-aranjuez-2026-david-porto-diaz-colocando-samuel.webp', 'eventos: Aranjuez documentary image missing or replaced by a generic asset');
  check(state.aranjuezOrganizerUrl === 'https://www.aranjuez.es/eres-autor-libreria-o-editorial-inscribete-en-la-feria-del-libro-de-aranjuez-2026/', 'eventos: Aranjuez organizer URL is not the official municipal source');
  await page.locator('#proximos').screenshot({ path: path.join(OUT, 'eventos-empty-1440.png') });
  await context.close();
}

// No-JS: public information remains readable on every route.
// These routes are measured for horizontal overflow, so they navigate with
// waitUntil 'load': at 'domcontentloaded' only one or two of the seven V1
// stylesheets have been applied and the page still lays out at its intrinsic
// desktop width, which reads as a ~1200px overflow that is not real.
for (const route of routes) {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, javaScriptEnabled: false });
  const page = await context.newPage();
  const response = await page.goto(BASE + route, { waitUntil: 'load' });
  check(response && response.ok(), `${route} no-JS: HTTP failure`);
  const state = await page.evaluate(() => ({
    text: document.querySelector('main')?.innerText.trim().length || 0,
    display: getComputedStyle(document.querySelector('main')).display,
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
  }));
  check(state.text > 200 && state.display !== 'none', `${route} no-JS: public content unavailable`);
  check(state.overflow <= 1, `${route} no-JS: horizontal overflow ${state.overflow}`);
  await context.close();
}

// Text-spacing override smoke test (WCAG 1.4.12 style fixture).
for (const route of routes) {
  const context = await newContext({ width: 390, height: 844 });
  const page = await context.newPage();
  await page.goto(BASE + route, { waitUntil: 'load' });
  await page.addStyleTag({ content: `*{line-height:1.5 !important;letter-spacing:.12em !important;word-spacing:.16em !important} p{margin-bottom:2em !important}` });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  check(overflow <= 1, `${route} text-spacing: horizontal overflow ${overflow}`);
  await context.close();
}

// Focus smoke: first Tab reaches the skip link in the public shell.
{
  const context = await newContext({ width: 390, height: 844 });
  const page = await context.newPage();
  await page.goto(BASE + '/autor.html', { waitUntil: 'domcontentloaded' });
  await page.keyboard.press('Tab');
  check(await page.locator('.skip-link').evaluate((el) => el === document.activeElement), 'a11y: first Tab does not focus skip link');
  await context.close();
}

// Required visual captures.
const shots = [
  ['/autor.html', 1440, 1000, 'autor-1440.png'],
  ['/autor.html', 390, 844, 'autor-390.png'],
  ['/prensa.html', 1440, 1000, 'prensa-1440.png'],
  ['/prensa.html', 390, 844, 'prensa-390.png'],
  ['/premios.html', 1440, 1000, 'premios-1440.png'],
  ['/eventos.html', 1440, 1000, 'eventos-1440.png'],
  ['/eventos.html', 390, 844, 'eventos-390.png'],
];
for (const [route, width, height, file] of shots) {
  const context = await newContext({ width, height });
  const page = await context.newPage();
  await page.goto(BASE + route, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(250);
  await page.screenshot({ path: path.join(OUT, file), fullPage: true });
  await context.close();
}

await fs.writeFile(path.join(OUT, 'browser-metrics.json'), JSON.stringify({ metrics, failures }, null, 2));
await browser.close();

if (failures.length) {
  console.error('\nIdentity public browser QA failed:');
  for (const message of failures) console.error(`- ${message}`);
  process.exit(1);
}
console.log(`Identity public browser QA PASS (${routes.length} routes, ${viewports.length} artboards).`);
