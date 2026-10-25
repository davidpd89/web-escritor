import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const START = new Date('2026-10-21T10:00:00.000Z');
const MS = START.getTime();
const COOLDOWN = 7 * 24 * 60 * 60 * 1000;
const KEY = 'nl-popup-ts';
const SUBSCRIBED = 'nl-subscribed';
const OPEN = '#nl-popup-dialog[open]';
const FAMILIES = [
  ['cuaderno', '/cuaderno/que-es-el-portal-fantasy/'],
  ['recomendaciones', '/recomendaciones/portal-fantasy-espanol/'],
  ['universo/noveris', '/universo/noveris/'],
  ['clubes-de-lectura', '/clubes-de-lectura/samuel-entre-mundos/']
];

function walk(directory) {
  assert.ok(fs.existsSync(directory), `Missing directory: ${directory}`);
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap(entry => {
    const filename = path.join(directory, entry.name);
    return entry.isDirectory() ? walk(filename) : entry.isFile() && entry.name.endsWith('.html') ? [filename] : [];
  });
}
function urlFor(filename) {
  return '/' + path.relative(ROOT, filename).split(path.sep).join('/').replace(/index\.html$/, '');
}
function hasPopup(filename) {
  return /<script\b[^>]*\bsrc\s*=\s*(['"])\/assets\/newsletter-popup\.js(?:\?[^'"]*)?\1/i.test(fs.readFileSync(filename, 'utf8'));
}
const routesByFamily = FAMILIES.map(([dir, baseline]) => {
  const routes = walk(path.join(ROOT, dir)).filter(hasPopup).map(urlFor).sort();
  assert.ok(routes.length, `${dir}: no popup-enabled HTML found`);
  assert.ok(routes.includes(baseline), `${dir}: missing popup in baseline ${baseline}`);
  return { dir, baseline, routes };
});
const ROUTES = [...new Set(routesByFamily.flatMap(family => family.routes))];
assert.equal(ROUTES.length, routesByFamily.reduce((sum, family) => sum + family.routes.length, 0), 'Overlapping family routes');
const SECONDARY = routesByFamily.flatMap(f => f.routes.filter(route => route !== f.baseline))[0];
assert.ok(SECONDARY, 'A secondary popup-enabled page is required for the negative control');
console.log('Popup-enabled route census:', JSON.stringify(Object.fromEntries(routesByFamily.map(f => [f.dir, f.routes.length]))));

const browser = await chromium.launch({ headless: true });
async function session() {
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    isMobile: true,
    hasTouch: true,
    reducedMotion: 'reduce',
    serviceWorkers: 'block'
  });
  await context.route('**/*', route => {
    const url = new URL(route.request().url());
    return url.origin === ORIGIN ? route.continue() : route.abort();
  });
  const page = await context.newPage();
  await page.clock.setFixedTime(START);
  const errors = [];
  page.on('pageerror', error => errors.push(String(error.stack || error)));
  return { context, page, errors };
}
function noErrors(errors, since, route) {
  assert.deepEqual(errors.slice(since), [], `${route}: uncaught browser page error`);
}
async function readStorage(page) {
  return page.evaluate(([key, subscribed]) => ({
    ts: localStorage.getItem(key), subscribed: localStorage.getItem(subscribed)
  }), [KEY, SUBSCRIBED]);
}
async function visit(sessionState, route) {
  const { page, errors } = sessionState;
  const since = errors.length;
  const runtimeResponses = [];
  const observe = response => {
    if (new URL(response.url()).pathname === '/assets/newsletter-popup.js') runtimeResponses.push(response.status());
  };
  page.on('response', observe);
  try {
    const response = await page.goto(ORIGIN + route, { waitUntil: 'domcontentloaded', timeout: 20000 });
    assert.ok(response?.ok(), `${route}: HTML navigation failed (${response?.status()})`);
    assert.equal(await page.locator('script[src^="/assets/newsletter-popup.js"]').count(), 1,
      `${route}: popup script not included exactly once`);
    assert.deepEqual(runtimeResponses, [200], `${route}: popup runtime did not load successfully`);
    noErrors(errors, since, route);
  } finally {
    page.off('response', observe);
  }
  return since;
}
async function triggerScroll(page, route) {
  const metrics = await page.evaluate(async () => {
    const frame = () => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    const max = document.documentElement.scrollHeight - innerHeight;
    if (max <= 0) return { max, ratio: 0 };
    scrollTo({ top: 0, behavior: 'instant' });
    await frame();
    scrollTo({ top: max, behavior: 'instant' });
    await frame();
    return { max, ratio: scrollY / Math.max(1, document.documentElement.scrollHeight - innerHeight) };
  });
  assert.ok(metrics.max > 0 && metrics.ratio >= 0.7, `${route}: cannot reach 70% scroll threshold: ${JSON.stringify(metrics)}`);
}
async function openPopup(state, route, since, expected = MS, timeout = 3500) {
  await triggerScroll(state.page, route);
  try {
    await state.page.locator(OPEN).waitFor({ state: 'visible', timeout });
  } catch {
    assert.fail(`${route}: popup did not open for a fresh visitor`);
  }
  assert.deepEqual(await readStorage(state.page), { ts: String(expected), subscribed: null },
    `${route}: opening must persist the exact fixed timestamp without a subscription flag`);
  noErrors(state.errors, since, route);
}
async function suppressed(state, route, since, expected) {
  await triggerScroll(state.page, route);
  // DOMContentLoaded includes deferred scripts; two animation frames above
  // allow scroll handlers to run, then this bounded window catches late opens.
  await state.page.waitForTimeout(350);
  assert.equal(await state.page.locator(OPEN).count(), 0, `${route}: popup reopened during cooldown`);
  assert.deepEqual(await readStorage(state.page), { ts: String(expected), subscribed: null },
    `${route}: existing cooldown timestamp or subscription flag changed`);
  noErrors(state.errors, since, route);
}
async function closePopup(page) {
  await page.locator('#nl-popup-close').click();
  await page.locator('#nl-popup-dialog').waitFor({ state: 'detached' });
}

try {
  // Full positive control for EVERY discovered route, not merely one per family.
  // Clearing only the timestamp between routes simulates a fresh visitor;
  // subscription state must remain absent throughout.
  const positive = await session();
  try {
    for (const route of ROUTES) {
      const since = await visit(positive, route);
      assert.deepEqual(await readStorage(positive.page), { ts: null, subscribed: null },
        `${route}: fresh visit must start without popup or subscription state`);
      await openPopup(positive, route, since);
      await closePopup(positive.page);
      assert.equal((await readStorage(positive.page)).ts, String(MS), `${route}: dismiss changed the fixed timestamp`);
      await positive.page.evaluate(key => localStorage.removeItem(key), KEY);
    }
  } finally {
    await positive.context.close();
  }

  // One visitor, one storage partition, across every enabled document.
  const shared = await session();
  try {
    const first = routesByFamily[0].baseline;
    let since = await visit(shared, first);
    await openPopup(shared, first, since);
    await closePopup(shared.page);
    for (const route of ROUTES) {
      since = await visit(shared, route);
      await suppressed(shared, route, since, MS);
    }
    const boundary = routesByFamily[1].baseline;
    await shared.page.clock.setFixedTime(new Date(MS + COOLDOWN - 1));
    since = await visit(shared, boundary);
    await suppressed(shared, boundary, since, MS);
    await shared.page.clock.setFixedTime(new Date(MS + COOLDOWN));
    since = await visit(shared, boundary);
    await openPopup(shared, boundary, since, MS + COOLDOWN);
    assert.equal((await readStorage(shared.page)).ts, String(MS + COOLDOWN),
      'At the exact seven-day boundary the popup must renew the timestamp');
  } finally {
    await shared.context.close();
  }

  // Negative control: suppress registration of the real popup scroll listener
  // on a secondary route. The same openPopup assertion MUST detect it.
  const broken = await session();
  try {
    await broken.context.addInitScript(() => {
      const original = window.addEventListener;
      window.addEventListener = function (type, callback, options) {
        if (type === 'scroll' && callback?.name === 'onScroll') {
          window.__qaBlockedNewsletterScroll = true;
          return;
        }
        return original.call(this, type, callback, options);
      };
    });
    const since = await visit(broken, SECONDARY);
    assert.equal(await broken.page.evaluate(() => window.__qaBlockedNewsletterScroll), true,
      'Negative-control fixture no longer blocks the popup scroll listener');
    await assert.rejects(() => openPopup(broken, SECONDARY, since, MS, 700),
      /popup did not open for a fresh visitor/,
      'The positive control failed to detect a broken secondary page');
    assert.deepEqual(await readStorage(broken.page), { ts: null, subscribed: null },
      'Negative control unexpectedly wrote popup storage');
    noErrors(broken.errors, since, SECONDARY);
  } finally {
    await broken.context.close();
  }

  console.log(`PASS: ${ROUTES.length} popup-enabled documents across ${FAMILIES.length} families; every route opens fresh and remains suppressed, exact seven-day renewal, broken-secondary control`);
} finally {
  await browser.close();
}
