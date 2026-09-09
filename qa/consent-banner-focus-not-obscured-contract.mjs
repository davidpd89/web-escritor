// Regression contract for a real bug reported live on mobile (2026-09-09):
// after passing the Home intro, the analytics-consent banner was invisible
// until scrolling deep into the page, then flickered visible/hidden on every
// further scroll depending on scroll position, and only ever appeared
// correctly right after a hard refresh.
//
// Root cause: assets/analytics-consent-banner.js's avoidObscuringFocus()
// (added for WCAG SC 2.4.11 Focus Not Obscured) shifts the banner down
// whenever document.activeElement's bounding box overlaps the banner's
// resting position. v1-shell.js moves focus to `<main id="contenido"
// tabindex="-1">` once the intro finishes closing -- a script-only focus
// sink, never reachable by Tab, with no visible focus ring for SC 2.4.11 to
// protect. But #contenido's bounding box spans the ENTIRE page (it wraps
// all main content), so the naive rect-overlap test always found it
// "overlapping" the banner's corner and shoved the banner down by a full
// viewport height -- literally off-screen below the fold. As the page was
// scrolled, that huge rect's viewport-relative position swept past the
// banner's fixed corner, flipping the overlap verdict back and forth on
// every scroll event (the reposition() function is wired to the scroll
// listener specifically for this feature). A refresh skips the intro
// entirely (sessionStorage already marks it seen) and never calls
// main.focus(), so activeElement stayed document.body and the early exit
// kicked in -- exactly why a refresh "fixed" it.
//
// The fix excludes any activeElement with tabIndex === -1 (a script-focus
// sink, not a real control) from the overlap check. This script verifies
// both halves of that contract: the sink itself is exempt (scenario 1, the
// literal repro), and a REAL focusable control that genuinely overlaps the
// banner still gets shifted -- proving the fix didn't just disable the
// feature (scenario 2).
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const MIME = new Map([
  ['.html', 'text/html; charset=utf-8'], ['.css', 'text/css; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'], ['.mjs', 'text/javascript; charset=utf-8'],
  ['.json', 'application/json; charset=utf-8'],
  ['.webp', 'image/webp'], ['.png', 'image/png'], ['.jpg', 'image/jpeg'], ['.avif', 'image/avif'],
  ['.svg', 'image/svg+xml'], ['.woff2', 'font/woff2'], ['.ico', 'image/x-icon'],
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
const ORIGIN = process.env.QA_ORIGIN || `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

const VIEWPORT = { width: 375, height: 812 };

async function getBannerState(page) {
  await page.waitForSelector('[data-analytics-consent-banner]', { timeout: 5000 });
  return page.evaluate(() => {
    const bar = document.querySelector('[data-analytics-consent-banner]');
    const r = bar.getBoundingClientRect();
    return { top: r.top, bottom: r.bottom, transform: bar.style.transform };
  });
}

try {
  // --- Scenario 1: the literal repro -- go through the real intro flow on
  // Home and confirm the banner lands fully inside the viewport, untouched.
  const context = await browser.newContext({ viewport: VIEWPORT });
  const page = await context.newPage();
  await page.goto(`${ORIGIN}/`, { waitUntil: 'load' });
  await page.evaluate(() => { try { localStorage.clear(); sessionStorage.clear(); } catch {} });
  await page.reload({ waitUntil: 'load' });

  const enter = page.locator('[data-intro-enter]');
  await enter.waitFor({ state: 'visible', timeout: 5000 });
  await enter.click();
  // v1-shell.js focuses #contenido ~820ms after the click (or 350ms under
  // reduced motion); give it real time to land before asserting.
  await page.waitForFunction(() => document.activeElement && document.activeElement.id === 'contenido', { timeout: 3000 });
  await page.waitForTimeout(400);

  const afterIntro = await getBannerState(page);
  assert.equal(afterIntro.transform, '',
    `after intro: banner has transform "${afterIntro.transform}" -- focusing the tabindex=-1 #contenido landmark must not shift it`);
  assert.ok(afterIntro.bottom <= VIEWPORT.height,
    `after intro: banner bottom is at ${afterIntro.bottom}px, viewport is only ${VIEWPORT.height}px -- banner is rendered off-screen`);
  assert.ok(afterIntro.top >= 0 && afterIntro.top < VIEWPORT.height,
    `after intro: banner top is at ${afterIntro.top}px -- not actually within the visible viewport`);

  await context.close();

  // --- Scenario 2: the feature must still work for a REAL control. Skip the
  // intro (already-seen, as a refresh would leave it) and focus a synthetic
  // focusable element deliberately placed exactly over the banner's resting
  // corner -- deterministic, unlike depending on real footer layout staying
  // put over time.
  const context2 = await browser.newContext({ viewport: VIEWPORT });
  const page2 = await context2.newPage();
  await page2.goto(`${ORIGIN}/`, { waitUntil: 'load' });
  await page2.evaluate(() => { try { sessionStorage.setItem('dp-intro-seen', '1'); localStorage.clear(); } catch {} });
  await page2.reload({ waitUntil: 'load' });
  await page2.waitForSelector('[data-analytics-consent-banner]', { timeout: 5000 });

  const restingRect = await page2.evaluate(() => {
    const bar = document.querySelector('[data-analytics-consent-banner]');
    return { left: bar.offsetLeft, top: bar.offsetTop, width: bar.offsetWidth, height: bar.offsetHeight };
  });

  await page2.evaluate((rect) => {
    const probe = document.createElement('a');
    probe.href = '#';
    probe.id = 'qa-focus-probe';
    probe.textContent = 'probe';
    probe.style.cssText = `position:fixed;left:${rect.left}px;top:${rect.top}px;width:${rect.width}px;height:${rect.height}px;`;
    document.body.appendChild(probe);
  }, restingRect);
  await page2.locator('#qa-focus-probe').focus();
  await page2.waitForTimeout(150);

  const withRealFocus = await getBannerState(page2);
  assert.notEqual(withRealFocus.transform, '',
    'a real, naturally-focusable control overlapping the banner must still trigger the SC 2.4.11 shift -- the tabIndex===-1 exemption must not have disabled the feature entirely');
  assert.ok(withRealFocus.top >= VIEWPORT.height || withRealFocus.bottom <= restingRect.top,
    `overlap shift should move the banner clear of its resting position (was top=${restingRect.top}, now top=${withRealFocus.top})`);

  await context2.close();
} finally {
  await browser.close();
  server.close();
}

console.log('consent-banner-focus-not-obscured-contract: OK');
