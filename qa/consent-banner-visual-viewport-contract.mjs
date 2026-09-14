// Regression contract for the visualViewport-aware repositioning added to
// assets/analytics-consent-banner.js (2026-09-08, PR #485).
//
// The bug: on mobile Safari/Android, position:fixed elements are placed
// against the LAYOUT viewport (window.innerHeight), which stays taller than
// the VISUAL viewport (window.visualViewport.height) while the browser's own
// UI (URL bar, bottom toolbar) is still fully expanded on first paint -- so a
// bottom-anchored banner can render below the actually-visible area until the
// visitor scrolls (which is what collapses the toolbar and lets the layout
// viewport catch up). The fix adds `visualViewportInset()`, the gap between
// innerHeight and the real visible height, as extra bottom offset.
//
// Headless Chromium's window.visualViewport never actually diverges from
// window.innerHeight on its own, so the PR's own manual QA only ever
// exercised the inset=0 case -- the exact scenario that motivated the fix
// was never covered. This script installs a fake VisualViewport (a real
// EventTarget so the code's own addEventListener("resize"/"scroll", ...)
// calls work unmodified) with a height/offsetTop that diverges from
// innerHeight, then drives it through resize/scroll updates and checks the
// banner's computed offset against the same formula the source uses.
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

// Real iPhone-class viewport: window.innerHeight stays at this fixed value
// throughout (Playwright's viewport, unlike a real phone, doesn't resize on
// its own) -- only the fake visualViewport moves, exactly isolating the
// divergence the fix is meant to handle.
const VIEWPORT = { width: 390, height: 844 };
const BASE_PX = 12; // matches the source's `let basePx = 12;` default

async function installFakeVisualViewport(page, { height, offsetTop }) {
  await page.addInitScript(({ height, offsetTop, width }) => {
    class FakeVisualViewport extends EventTarget {
      constructor(h, o, w) {
        super();
        this.height = h;
        this.offsetTop = o;
        this.width = w;
        this.offsetLeft = 0;
        this.scale = 1;
      }
    }
    const vv = new FakeVisualViewport(height, offsetTop, width);
    window.__fakeVisualViewport = vv;
    Object.defineProperty(window, 'visualViewport', { value: vv, configurable: true });
  }, { height, offsetTop, width: VIEWPORT.width });
}

function updateFakeVisualViewport(page, { height, offsetTop, eventType }) {
  return page.evaluate(({ height, offsetTop, eventType }) => {
    const vv = window.__fakeVisualViewport;
    if (typeof height === 'number') vv.height = height;
    if (typeof offsetTop === 'number') vv.offsetTop = offsetTop;
    vv.dispatchEvent(new Event(eventType));
  }, { height, offsetTop, eventType });
}

async function getBannerBottomPx(page) {
  await page.waitForSelector('[data-analytics-consent-banner]', { timeout: 5000 });
  return page.evaluate(() => {
    const bar = document.querySelector('[data-analytics-consent-banner]');
    return parseFloat(bar.style.bottom || '0');
  });
}

function expectedInset({ innerHeight, vvHeight, vvOffsetTop }) {
  return Math.max(0, innerHeight - (vvHeight + vvOffsetTop));
}

try {
  const context = await browser.newContext({ viewport: VIEWPORT });
  const page = await context.newPage();

  // --- Scenario 1: first paint, visualViewport shorter than innerHeight
  // (collapsed-toolbar case) -- the exact bug report ("only shows up once I
  // scroll all the way down").
  const firstPaint = { height: 700, offsetTop: 0 };
  await installFakeVisualViewport(page, firstPaint);
  await page.goto(`${ORIGIN}/fragmento/`, { waitUntil: 'load' });
  await page.waitForTimeout(600);

  const inset1 = expectedInset({ innerHeight: VIEWPORT.height, vvHeight: firstPaint.height, vvOffsetTop: firstPaint.offsetTop });
  assert.ok(inset1 > 0, 'test setup: expected a non-zero inset for the first-paint scenario');
  const bottom1 = await getBannerBottomPx(page);
  assert.equal(bottom1, BASE_PX + inset1,
    `first paint: banner bottom offset is ${bottom1}px, expected ${BASE_PX + inset1}px (base ${BASE_PX} + inset ${inset1})`);
  assert.ok(await page.locator('[data-analytics-consent-banner]').isVisible(),
    'first paint: banner must be visible without needing a scroll first');

  // --- Scenario 2: visualViewport.resize -- toolbar finishes collapsing
  // (or the on-screen keyboard opens), shrinking further.
  await updateFakeVisualViewport(page, { height: 620, eventType: 'resize' });
  await page.waitForTimeout(100);
  const inset2 = expectedInset({ innerHeight: VIEWPORT.height, vvHeight: 620, vvOffsetTop: firstPaint.offsetTop });
  const bottom2 = await getBannerBottomPx(page);
  assert.equal(bottom2, BASE_PX + inset2,
    `visualViewport resize: banner bottom offset is ${bottom2}px, expected ${BASE_PX + inset2}px`);
  assert.notEqual(bottom2, bottom1, 'visualViewport resize: offset did not actually change -- reposition() may not be wired to the resize listener');

  // --- Scenario 3: visualViewport.scroll -- offsetTop moves (e.g. the
  // visual viewport panning while a keyboard is open).
  await updateFakeVisualViewport(page, { offsetTop: 40, eventType: 'scroll' });
  await page.waitForTimeout(100);
  const inset3 = expectedInset({ innerHeight: VIEWPORT.height, vvHeight: 620, vvOffsetTop: 40 });
  const bottom3 = await getBannerBottomPx(page);
  assert.equal(bottom3, BASE_PX + inset3,
    `visualViewport scroll: banner bottom offset is ${bottom3}px, expected ${BASE_PX + inset3}px`);
  assert.notEqual(bottom3, bottom2, 'visualViewport scroll: offset did not actually change -- reposition() may not be wired to the scroll listener');

  await context.close();

  // --- Scenario 4: coexistence with #sticky-cta (fragmento is the one page
  // that ships both). Scroll into the window where sticky-cta shows itself,
  // then confirm the banner's offset accounts for BOTH the sticky bar and
  // the visualViewport inset at the same time, not just whichever ran last.
  const context2 = await browser.newContext({ viewport: VIEWPORT });
  const page2 = await context2.newPage();
  const stickyScenario = { height: 700, offsetTop: 0 };
  await installFakeVisualViewport(page2, stickyScenario);
  await page2.goto(`${ORIGIN}/fragmento/`, { waitUntil: 'load' });
  await page2.waitForTimeout(600);

  const totalScroll = await page2.evaluate(() => document.body.scrollHeight - window.innerHeight);
  assert.ok(totalScroll > 0, 'test setup: fragmento page is not tall enough to trigger #sticky-cta by scrolling');
  await page2.evaluate((y) => window.scrollTo(0, y), Math.floor(totalScroll * 0.75));
  await page2.waitForFunction(() => document.getElementById('sticky-cta').classList.contains('visible'), { timeout: 5000 });
  // #sticky-cta slides in via a 220ms CSS transform transition -- wait for it
  // to finish so its measured rect is the settled one, exactly as the
  // source's own transitionend handler expects.
  await page2.waitForTimeout(400);

  const stickyRectTop = await page2.evaluate(() => document.getElementById('sticky-cta').getBoundingClientRect().top);
  const expectedBasePx = Math.max(BASE_PX, VIEWPORT.height - stickyRectTop + BASE_PX);
  const insetSticky = expectedInset({ innerHeight: VIEWPORT.height, vvHeight: stickyScenario.height, vvOffsetTop: stickyScenario.offsetTop });
  const bottomSticky = await getBannerBottomPx(page2);
  assert.ok(Math.abs(bottomSticky - (expectedBasePx + insetSticky)) < 0.01,
    `sticky-cta + visualViewport: banner bottom offset is ${bottomSticky}px, expected ${expectedBasePx + insetSticky}px ` +
    `(sticky-adjusted base ${expectedBasePx} + inset ${insetSticky}) -- one of the two offsets is being dropped instead of summed`);

  await context2.close();
} finally {
  await browser.close();
  server.close();
}

console.log('consent-banner-visual-viewport-contract: OK');
