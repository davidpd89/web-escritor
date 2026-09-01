import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const BASE = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const OUT = process.env.RECOMMENDATIONS_ARTIFACT_DIR || 'artifacts/recommendations';
const routes = [
  { path: '/recomendaciones/', kind: 'hub' },
  { path: '/recomendaciones/portal-fantasy-espanol/', kind: 'list', count: 10 },
  { path: '/recomendaciones/magia-con-coste/', kind: 'list', count: 6 },
];
const viewports = [
  { name: '320', width: 320, height: 900 },
  { name: '390', width: 390, height: 900 },
  { name: '768', width: 768, height: 1000 },
  { name: '1024', width: 1024, height: 900 },
  { name: '1440', width: 1440, height: 1000 },
  { name: '1728', width: 1728, height: 1000 },
  { name: 'landscape-844x390', width: 844, height: 390 },
];

const failures = [];
const metrics = [];
const fail = (message) => failures.push(message);
const check = (value, message) => { if (!value) fail(message); };
const norm = (value = '') => value.replace(/[\s\u00a0]+/g, ' ').trim();
const loose = (value = '') => norm(value).toLocaleLowerCase('es').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, ' ').trim();

function validISBN10(raw) {
  const s = raw.replace(/[-\s]/g, '').toUpperCase();
  if (!/^\d{9}[\dX]$/.test(s)) return false;
  let sum = 0;
  for (let i = 0; i < 10; i++) sum += (10 - i) * (s[i] === 'X' ? 10 : Number(s[i]));
  return sum % 11 === 0;
}
function validISBN13(raw) {
  const s = raw.replace(/[-\s]/g, '');
  if (!/^\d{13}$/.test(s)) return false;
  let sum = 0;
  for (let i = 0; i < 12; i++) sum += Number(s[i]) * (i % 2 ? 3 : 1);
  return (10 - (sum % 10)) % 10 === Number(s[12]);
}
function validISBN(raw) { return validISBN10(raw) || validISBN13(raw); }

await fs.mkdir(OUT, { recursive: true });
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

async function contextFor(viewport, extra = {}) {
  return browser.newContext({ viewport: { width: viewport.width, height: viewport.height }, reducedMotion: 'reduce', ...extra });
}

async function openChecked(context, route) {
  const page = await context.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  const brokenLocal = [];
  await page.addInitScript(() => {
    window.__recCLS = 0;
    try {
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) if (!entry.hadRecentInput) window.__recCLS += entry.value;
      }).observe({ type: 'layout-shift', buffered: true });
    } catch (_) {}
  });
  page.on('console', (msg) => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });
  page.on('pageerror', (error) => pageErrors.push(error.message));
  page.on('response', (response) => {
    const u = new URL(response.url());
    if (u.origin === new URL(BASE).origin && response.status() >= 400) brokenLocal.push(`${response.status()} ${u.pathname}`);
  });
  const response = await page.goto(BASE + route, { waitUntil: 'load' });
  check(response?.ok(), `${route}: HTTP ${response?.status() ?? 'no response'}`);
  await page.waitForTimeout(350);
  const state = await page.evaluate(() => ({
    width: document.documentElement.scrollWidth,
    client: document.documentElement.clientWidth,
    text: document.querySelector('main')?.innerText.trim().length || 0,
    cls: window.__recCLS || 0,
  }));
  check(state.text > 250, `${route}: main content unexpectedly short`);
  check(consoleErrors.length === 0, `${route}: console errors: ${consoleErrors.join(' | ')}`);
  check(pageErrors.length === 0, `${route}: page errors: ${pageErrors.join(' | ')}`);
  check(brokenLocal.length === 0, `${route}: broken local assets: ${[...new Set(brokenLocal)].join(', ')}`);
  return { page, state };
}

// Fresh browser context for every required viewport and route.
for (const vp of viewports) {
  for (const route of routes) {
    const context = await contextFor(vp);
    const { state } = await openChecked(context, route.path);
    check(state.width <= state.client + 1, `${route.path} @ ${vp.name}: horizontal overflow ${state.width}/${state.client}`);
    check(state.cls <= 0.1, `${route.path} @ ${vp.name}: CLS ${state.cls.toFixed(4)} > 0.1`);
    metrics.push({ route: route.path, viewport: vp.name, overflow: state.width - state.client, cls: state.cls });
    await context.close();
  }
}

// Hub: two curated collections, author context separate, no fake current Cuaderno.
{
  const context = await contextFor({ width: 1440, height: 1000 });
  const { page } = await openChecked(context, '/recomendaciones/');
  const hub = await page.evaluate(() => {
    const docs = [...document.querySelectorAll('script[type="application/ld+json"]')].map((s) => JSON.parse(s.textContent));
    const nodes = docs.flatMap((d) => d['@graph'] || [d]);
    const list = nodes.find((n) => n['@type'] === 'ItemList');
    return {
      visibleLists: document.querySelectorAll('.recommendations-index > li').length,
      authorContext: Boolean(document.querySelector('.recommendations-author-context a[href="/libros/samuel-entre-mundos/"]')),
      genericCards: document.querySelectorAll('.id-cards > .id-card').length,
      primaryCurrent: [...document.querySelectorAll('.primary-nav [aria-current="page"]')].map((a) => a.getAttribute('href')),
      schemaCount: list?.numberOfItems,
      schemaItems: list?.itemListElement?.length,
      urls: [...document.querySelectorAll('.recommendations-index a[href^="/recomendaciones/"]')].map((a) => a.getAttribute('href')),
    };
  });
  check(hub.visibleLists === 2, `hub: expected 2 curated lists, got ${hub.visibleLists}`);
  check(hub.schemaCount === 2 && hub.schemaItems === 2, 'hub: ItemList count is not 2/2');
  check(hub.authorContext, 'hub: Samuel author-context link missing');
  check(hub.genericCards === 0, 'hub: generic 3-card product-like grid still present');
  check(hub.primaryCurrent.length === 0, `hub: primary nav has false aria-current ${hub.primaryCurrent.join(', ')}`);
  check(hub.urls.includes('/recomendaciones/portal-fantasy-espanol/') && hub.urls.includes('/recomendaciones/magia-con-coste/'), 'hub: curated list links missing');
  await context.close();
}

// #282: azul/dorado como jerarquia editorial, no como fondo de producto.
// Ledger metrics stay neutral; disclosure/positions/eyebrows/h1 take the
// family palette. Also confirms the layer never leaks outside its 4 routes.
const REC_BLUE = 'rgb(29, 79, 150)';
const REC_GOLD = 'rgb(184, 134, 11)';
{
  const context = await contextFor({ width: 1440, height: 1000 });
  const { page } = await openChecked(context, '/recomendaciones/');
  const hubColors = await page.evaluate(() => ({
    h1: getComputedStyle(document.querySelector('.recommendations-hero h1')).color,
    eyebrow: getComputedStyle(document.querySelector('.recommendations-hero .eyebrow')).color,
    number: getComputedStyle(document.querySelector('.recommendations-index__number')).color,
  }));
  check(hubColors.h1 === REC_BLUE, `hub: h1 should use editorial blue, got ${hubColors.h1}`);
  check(hubColors.eyebrow === REC_GOLD, `hub: eyebrow should use editorial gold, got ${hubColors.eyebrow}`);
  check(hubColors.number === REC_BLUE, `hub: folio number should use editorial blue, got ${hubColors.number}`);
  await context.close();
}
for (const route of ['/recomendaciones/portal-fantasy-espanol/', '/recomendaciones/magia-con-coste/', '/recomendaciones/politica-de-recomendaciones/']) {
  const context = await contextFor({ width: 1440, height: 1000 });
  const { page } = await openChecked(context, route);
  const colors = await page.evaluate(() => ({
    h1: getComputedStyle(document.querySelector('.article-header h1')).color,
    eyebrow: getComputedStyle(document.querySelector('.article-header .eyebrow')).color,
    hasIdentity: !!document.querySelector('link[href="/assets/v1-recommendations.css"]'),
  }));
  check(colors.h1 === REC_BLUE, `${route}: h1 should use editorial blue, got ${colors.h1}`);
  check(colors.eyebrow === REC_GOLD, `${route}: eyebrow should use editorial gold, got ${colors.eyebrow}`);
  check(colors.hasIdentity, `${route}: must load v1-recommendations.css`);
  if (route !== '/recomendaciones/politica-de-recomendaciones/') {
    const listColors = await page.evaluate(() => ({
      position: getComputedStyle(document.querySelector('.rec-position')).color,
      disclosureBorder: getComputedStyle(document.querySelector('.rec-disclosures')).borderLeftColor,
      firstBookValue: getComputedStyle(document.querySelector('.rec-book-title')).color,
    }));
    check(listColors.position === REC_BLUE, `${route}: position number should use editorial blue, got ${listColors.position}`);
    check(listColors.disclosureBorder === REC_BLUE, `${route}: disclosure rail should use editorial blue, got ${listColors.disclosureBorder}`);
    check(listColors.firstBookValue !== REC_BLUE && listColors.firstBookValue !== REC_GOLD, `${route}: book titles must stay neutral, not recolored`);
  }
  await context.close();
}
// Isolation: real /cuaderno/ articles and the hub /herramientas/ never load this layer.
for (const outOfScope of ['/cuaderno/', '/herramientas/']) {
  const context = await contextFor({ width: 1440, height: 1000 });
  const { page } = await openChecked(context, outOfScope);
  const leaked = await page.evaluate(() => !!document.querySelector('link[href="/assets/v1-recommendations.css"]'));
  check(!leaked, `${outOfScope}: must NOT load v1-recommendations.css`);
  await context.close();
}

async function inspectList(route, expectedCount) {
  const context = await contextFor({ width: 1440, height: 1000 });
  const { page } = await openChecked(context, route);
  const data = await page.evaluate(() => {
    const docs = [...document.querySelectorAll('script[type="application/ld+json"]')].map((s) => JSON.parse(s.textContent));
    const nodes = docs.flatMap((d) => d['@graph'] || [d]);
    const itemList = nodes.find((n) => n['@type'] === 'ItemList');
    const visible = [...document.querySelectorAll('[data-recommendation-list] > .rec-item')].map((el) => ({
      pos: Number(el.dataset.position),
      isbn: el.dataset.isbn || '',
      title: el.querySelector('.rec-book-title a')?.textContent || '',
      author: el.querySelector('.rec-book-author')?.textContent || '',
      url: el.querySelector('.rec-book-title a')?.href || '',
      meta: el.querySelector('.rec-book-meta')?.textContent || '',
    }));
    const schema = (itemList?.itemListElement || []).map((entry) => ({
      pos: entry.position,
      isbn: entry.item?.isbn || '',
      title: entry.item?.name || '',
      authors: Array.isArray(entry.item?.author) ? entry.item.author.map((a) => a.name) : [entry.item?.author?.name].filter(Boolean),
      url: entry.item?.url || '',
    }));
    const visibleFaq = [...document.querySelectorAll('#faq details')].map((d) => ({
      q: d.querySelector('summary')?.textContent || '',
      a: [...d.querySelectorAll(':scope > p, :scope > div, :scope > ul, :scope > ol')].map((el) => el.textContent || '').join(' '),
      hasSummary: Boolean(d.querySelector(':scope > summary')),
    }));
    const firstAffiliateTop = document.querySelector('.rec-item a[href*="amazon.es"]')?.getBoundingClientRect().top ?? Infinity;
    const disclosureBottom = document.querySelector('.rec-disclosures')?.getBoundingClientRect().bottom ?? -Infinity;
    return {
      visible,
      schema,
      itemListCount: itemList?.numberOfItems,
      visibleFaq,
      hasFaqPage: nodes.some((n) => n['@type'] === 'FAQPage'),
      primaryCurrent: [...document.querySelectorAll('.primary-nav [aria-current="page"]')].map((a) => a.getAttribute('href')),
      affiliateLinks: [...document.querySelectorAll('a[href*="amazon.es"]')].map((a) => ({ href: a.href, rel: a.rel, target: a.target })),
      affiliateDisclosure: document.querySelector('.rec-disclosures')?.innerText || '',
      selfText: document.querySelector('.rec-item--self')?.innerText || '',
      selfSpecialPrimary: document.querySelectorAll('.rec-item--self .primary-action').length,
      firstAffiliateTop,
      disclosureBottom,
      title: document.title,
      h1: document.querySelector('h1')?.textContent || '',
      og: document.querySelector('meta[property="og:title"]')?.content || '',
      twitter: document.querySelector('meta[name="twitter:title"]')?.content || '',
      listName: itemList?.name || '',
    };
  });

  check(data.visible.length === expectedCount, `${route}: visible count ${data.visible.length} != ${expectedCount}`);
  check(data.itemListCount === expectedCount, `${route}: numberOfItems ${data.itemListCount} != ${expectedCount}`);
  check(data.schema.length === expectedCount, `${route}: schema item count ${data.schema.length} != ${expectedCount}`);
  const expectedPositions = Array.from({ length: expectedCount }, (_, i) => i + 1);
  check(JSON.stringify(data.visible.map((x) => x.pos)) === JSON.stringify(expectedPositions), `${route}: visible positions are not 1..N`);
  check(JSON.stringify(data.schema.map((x) => x.pos)) === JSON.stringify(expectedPositions), `${route}: schema positions are not 1..N`);
  check(new Set(data.visible.map((x) => x.pos)).size === expectedCount, `${route}: duplicate visible positions`);
  check(new Set(data.schema.map((x) => x.pos)).size === expectedCount, `${route}: duplicate schema positions`);

  for (let i = 0; i < expectedCount; i++) {
    const v = data.visible[i];
    const s = data.schema[i];
    check(loose(v.title) === loose(s.title), `${route} #${i + 1}: visible/schema title mismatch: ${v.title} <> ${s.title}`);
    check(v.isbn === s.isbn, `${route} #${i + 1}: visible/schema ISBN mismatch ${v.isbn} <> ${s.isbn}`);
    check(Boolean(v.isbn) && validISBN(v.isbn), `${route} #${i + 1}: invalid/missing ISBN ${v.isbn}`);
    check(norm(v.meta).includes(v.isbn), `${route} #${i + 1}: ISBN not visible in edition line`);
    for (const author of s.authors) check(loose(v.author).includes(loose(author)), `${route} #${i + 1}: visible author missing ${author}`);
    check(v.url === s.url, `${route} #${i + 1}: visible/schema external URL mismatch`);
  }

  // FAQ is intentionally human-visible only. FAQPage legacy must stay absent;
  // the browser contract validates the visible FAQ as content/structure,
  // rather than comparing it with a schema node that no longer exists.
  check(data.hasFaqPage === false, `${route}: legacy FAQPage schema must be absent`);
  check(data.visibleFaq.length > 0, `${route}: visible FAQ unexpectedly missing`);
  const faqQuestions = new Set();
  for (let i = 0; i < data.visibleFaq.length; i++) {
    const item = data.visibleFaq[i];
    check(item.hasSummary, `${route}: FAQ item ${i + 1} has no direct summary`);
    check(norm(item.q).length >= 8, `${route}: FAQ question ${i + 1} is empty/too short`);
    check(norm(item.a).length >= 20, `${route}: FAQ answer ${i + 1} is empty/too short`);
    const key = loose(item.q);
    check(!faqQuestions.has(key), `${route}: duplicate visible FAQ question ${i + 1}`);
    faqQuestions.add(key);
  }

  check(data.primaryCurrent.length === 0, `${route}: false primary-nav aria-current ${data.primaryCurrent.join(', ')}`);
  check(data.affiliateLinks.length >= expectedCount, `${route}: expected affiliate links for each entry`);
  for (const link of data.affiliateLinks) {
    const u = new URL(link.href);
    const rel = new Set(link.rel.split(/\s+/).filter(Boolean));
    check(u.protocol === 'https:' && u.hostname === 'www.amazon.es', `${route}: affiliate host/protocol invalid ${link.href}`);
    check(u.searchParams.get('tag') === 'davidporto-21', `${route}: affiliate tag missing ${link.href}`);
    for (const token of ['sponsored', 'nofollow', 'noopener', 'noreferrer']) check(rel.has(token), `${route}: affiliate rel missing ${token}: ${link.href}`);
    check(link.target === '_blank', `${route}: external affiliate target is not _blank`);
  }
  check(/afiliad/i.test(data.affiliateDisclosure) && /comisi/i.test(data.affiliateDisclosure), `${route}: affiliate disclosure missing/unclear`);
  check(data.disclosureBottom <= data.firstAffiliateTop + 1, `${route}: disclosure appears after commerce links`);
  check(/obra del autor de esta web/i.test(data.selfText), `${route}: Samuel conflict-of-interest label missing`);
  check(data.selfSpecialPrimary === 0, `${route}: Samuel receives a privileged primary CTA`);
  for (const surface of [data.title, data.h1, data.og, data.twitter, data.listName]) check(new RegExp(`\\b${expectedCount}\\b`).test(surface), `${route}: count ${expectedCount} missing from metadata surface: ${surface}`);
  await context.close();
}

await inspectList('/recomendaciones/portal-fantasy-espanol/', 10);
await inspectList('/recomendaciones/magia-con-coste/', 6);

// Text spacing at 390px and 200% CSS zoom, each in a fresh context.
for (const route of routes) {
  const context = await contextFor({ width: 390, height: 900 });
  const page = await context.newPage();
  await page.goto(BASE + route.path, { waitUntil: 'load' });
  await page.addStyleTag({ content: '*{line-height:1.5 !important;letter-spacing:.12em !important;word-spacing:.16em !important} p{margin-bottom:2em !important}' });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  check(overflow <= 1, `${route.path}: WCAG text-spacing overflow ${overflow}`);
  await context.close();

  const zoomContext = await contextFor({ width: 390, height: 900 });
  const zoomPage = await zoomContext.newPage();
  await zoomPage.goto(BASE + route.path, { waitUntil: 'load' });
  await zoomPage.addStyleTag({ content: 'html{zoom:2}' });
  const zoomState = await zoomPage.evaluate(() => ({ body: document.body.scrollWidth, doc: document.documentElement.clientWidth, main: document.querySelector('main')?.innerText.length || 0 }));
  check(zoomState.main > 250, `${route.path}: content lost at 200% zoom`);
  check(zoomState.body <= zoomState.doc * 2 + 2, `${route.path}: unexpected 200% zoom overflow ${zoomState.body}/${zoomState.doc}`);
  await zoomContext.close();
}

// No-JS content remains available.
for (const route of routes) {
  const context = await browser.newContext({ viewport: { width: 390, height: 900 }, javaScriptEnabled: false });
  const page = await context.newPage();
  const response = await page.goto(BASE + route.path, { waitUntil: 'load' });
  check(response?.ok(), `${route.path} no-JS: HTTP failure`);
  const state = await page.evaluate(() => ({ text: document.querySelector('main')?.innerText.trim().length || 0, display: getComputedStyle(document.querySelector('main')).display, overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth }));
  check(state.text > 250 && state.display !== 'none', `${route.path} no-JS: content unavailable`);
  check(state.overflow <= 1, `${route.path} no-JS: horizontal overflow ${state.overflow}`);
  await context.close();
}

// Keyboard: skip link first, Explore opens and closes by keyboard.
{
  const context = await contextFor({ width: 390, height: 900 });
  const page = await context.newPage();
  await page.goto(BASE + '/recomendaciones/portal-fantasy-espanol/', { waitUntil: 'load' });
  await page.keyboard.press('Tab');
  check(await page.locator('.skip-link').evaluate((el) => el === document.activeElement), 'keyboard: first Tab does not focus skip link');
  await page.locator('[data-explore-open]').focus();
  await page.keyboard.press('Enter');
  check(await page.locator('[data-explore-dialog]').evaluate((el) => el.open), 'keyboard: Explore did not open with Enter');
  await page.keyboard.press('Escape');
  check(!(await page.locator('[data-explore-dialog]').evaluate((el) => el.open)), 'keyboard: Explore did not close with Escape');
  await context.close();
}

// Share/print tools become available with JS; print preserves editorial content and disclosures.
{
  const context = await contextFor({ width: 1440, height: 1000 });
  const page = await context.newPage();
  await page.goto(BASE + '/recomendaciones/portal-fantasy-espanol/', { waitUntil: 'load' });
  await page.waitForTimeout(250);
  check(await page.locator('[data-share-url]').isVisible(), 'share: control not visible after JS initialization');
  check(await page.locator('[data-print]').isVisible(), 'print: control not visible after JS initialization');
  await page.emulateMedia({ media: 'print' });
  const print = await page.evaluate(() => ({
    header: getComputedStyle(document.querySelector('.site-header')).display,
    footer: getComputedStyle(document.querySelector('.site-footer')).display,
    title: document.querySelector('#article-title')?.innerText || '',
    books: [...document.querySelectorAll('.rec-book-title')].filter((el) => getComputedStyle(el).display !== 'none' && el.innerText.trim()).length,
    disclosure: getComputedStyle(document.querySelector('.rec-disclosures')).display,
  }));
  check(print.header === 'none', 'print: interactive header not hidden');
  check(print.footer === 'none', 'print: site footer not hidden');
  check(print.title.includes('10 libros'), 'print: title missing');
  check(print.books === 10, `print: expected 10 visible book titles, got ${print.books}`);
  check(print.disclosure !== 'none', 'print: disclosure hidden');
  await page.screenshot({ path: path.join(OUT, 'portal-print.png'), fullPage: true });
  await context.close();
}

// Required screenshots.
const shots = [
  ['/recomendaciones/', 1440, 1000, 'hub-1440.png'],
  ['/recomendaciones/', 390, 900, 'hub-390.png'],
  ['/recomendaciones/portal-fantasy-espanol/', 1440, 1000, 'portal-1440.png'],
  ['/recomendaciones/portal-fantasy-espanol/', 390, 900, 'portal-390.png'],
  ['/recomendaciones/magia-con-coste/', 1440, 1000, 'magia-1440.png'],
  ['/recomendaciones/magia-con-coste/', 390, 900, 'magia-390.png'],
];
for (const [route, width, height, file] of shots) {
  const context = await contextFor({ width, height });
  const page = await context.newPage();
  await page.goto(BASE + route, { waitUntil: 'load' });
  await page.waitForTimeout(250);
  await page.screenshot({ path: path.join(OUT, file), fullPage: true });
  await context.close();
}

await fs.writeFile(path.join(OUT, 'browser-metrics.json'), JSON.stringify({ metrics, failures }, null, 2));
await browser.close();

if (failures.length) {
  console.error('\nRecommendations browser QA failed:');
  for (const message of failures) console.error(`- ${message}`);
  process.exit(1);
}
console.log(`Recommendations browser QA PASS (${routes.length} routes, ${viewports.length} artboards).`);