// Regression coverage for the 2026-09-16 finding: script.js gates
// Clarity/GoatCounter/Metricool with a PRODUCTION HOSTNAME ALLOWLIST
// (ANALYTICS_PRODUCTION_HOST), not a blocklist of known-bad environments.
// The allowlist replaced an earlier blocklist (localhost/127.0.0.1/file:)
// that shipped in #516/#518: that blocklist was itself found to have a real
// gap the same week -- STAGING_HOSTNAMES (script.js, used to disable the
// newsletter form on the Cloudflare Pages preview) was never added to it,
// so opening the staging preview kept sending real traffic to production
// Clarity/GoatCounter/Metricool. Nothing in the existing qa/*.mjs suite
// exercised a staging or production *hostname* -- every browser suite
// serves content from 127.0.0.1, which happened to be blocked either way,
// so this specific gap could not have been caught by rerunning them.
//
// This suite fakes three hostnames (production, the real staging preview
// host, and a plausible unknown-future-preview host) via Playwright request
// interception -- no real DNS or live server needed for that, Chromium's
// route interception happens before the actual network connection -- and
// asserts the tracker network calls that actually fire from each.
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const MIME = new Map([
  ['.html', 'text/html; charset=utf-8'], ['.css', 'text/css; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'], ['.webp', 'image/webp'], ['.png', 'image/png'],
  ['.jpg', 'image/jpeg'], ['.svg', 'image/svg+xml'], ['.woff2', 'font/woff2'], ['.ico', 'image/x-icon'],
]);

async function serveFakeOrigin(context, origin) {
  await context.route(`${origin}/**`, async (route) => {
    const url = new URL(route.request().url());
    let clean = decodeURIComponent(url.pathname.split('?')[0]).replace(/^\/+/, '');
    if (clean === '' || clean.endsWith('/')) clean += 'index.html';
    const file = path.join(ROOT, clean);
    if (!fs.existsSync(file) || !fs.statSync(file).isFile()) {
      await route.fulfill({ status: 404, body: 'not found' });
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: MIME.get(path.extname(file).toLowerCase()) || 'application/octet-stream',
      body: fs.readFileSync(file),
    });
  });
}

async function trackerAttempts(context) {
  const seen = { goatcounter: 0, metricool: 0, clarity: 0 };
  await context.route(/gc\.zgo\.at\/count\.js/, (route) => { seen.goatcounter++; route.abort(); });
  await context.route(/tracker\.metricool\.com\/resources\/be\.js/, (route) => { seen.metricool++; route.abort(); });
  await context.route(/clarity\.ms\/tag\//, (route) => { seen.clarity++; route.abort(); });
  return seen;
}

const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

async function visit(origin) {
  const context = await browser.newContext();
  const seen = await trackerAttempts(context);
  await serveFakeOrigin(context, origin);
  const page = await context.newPage();
  await page.goto(`${origin}/`, { waitUntil: 'load' });
  // scheduleBackgroundIdle's scheduler.postTask("background") path (real
  // Chromium has Scheduler API) needs to actually get a turn; 1s is well
  // past its 2000ms requestIdleCallback timeout fallback too, so this also
  // exercises that this deferral doesn't quietly never fire.
  await page.waitForTimeout(1000);
  await context.close();
  return seen;
}

try {
  {
    const seen = await visit('https://davidportodiaz.com');
    assert.equal(seen.goatcounter, 1, `production must load GoatCounter exactly once, saw ${seen.goatcounter}`);
    assert.equal(seen.metricool, 1, `production must load Metricool exactly once, saw ${seen.metricool}`);
    assert.equal(seen.clarity, 1, `production must load Clarity exactly once, saw ${seen.clarity}`);
  }
  {
    const seen = await visit('https://www.davidportodiaz.com');
    assert.equal(seen.goatcounter, 1, `www production must load GoatCounter exactly once, saw ${seen.goatcounter}`);
    assert.equal(seen.metricool, 1, `www production must load Metricool exactly once, saw ${seen.metricool}`);
    assert.equal(seen.clarity, 1, `www production must load Clarity exactly once, saw ${seen.clarity}`);
  }
  {
    // The real, currently-configured Cloudflare Pages preview hostname
    // (STAGING_HOSTNAMES in script.js) -- this is the exact gap found
    // 2026-09-16: the old blocklist let this one through.
    const seen = await visit('https://david-porto-preview.davidpd89.workers.dev');
    assert.equal(seen.goatcounter, 0, `staging must not load GoatCounter, saw ${seen.goatcounter}`);
    assert.equal(seen.metricool, 0, `staging must not load Metricool, saw ${seen.metricool}`);
    assert.equal(seen.clarity, 0, `staging must not load Clarity, saw ${seen.clarity}`);
  }
  {
    // Any other hostname (a hypothetical future preview/CI domain nobody
    // remembered to blocklist) -- this is exactly the class of gap an
    // allowlist closes structurally instead of case-by-case.
    const seen = await visit('https://some-future-preview.pages.dev');
    assert.equal(seen.goatcounter, 0, `unknown hostname must not load GoatCounter, saw ${seen.goatcounter}`);
    assert.equal(seen.metricool, 0, `unknown hostname must not load Metricool, saw ${seen.metricool}`);
    assert.equal(seen.clarity, 0, `unknown hostname must not load Clarity, saw ${seen.clarity}`);
  }
  console.log('analytics-hostname-allowlist-browser: PASS');
} finally {
  await browser.close();
}
