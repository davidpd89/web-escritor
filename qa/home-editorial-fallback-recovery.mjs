// Regression for a real, live-reproduced bug (2026-09-04): index.html hides
// .river-grid/.promo-band/#faq/#newsletter until assets/v1-home-editorial-v3.js's
// buildFlow() sets data-home-editorial-v3="true" as its last step, with
// <noscript> as the only pre-existing escape hatch (for JS-disabled
// visitors). If that module -- or its static `import` of
// editorial-public-facts.mjs -- fails to load for a JS-enabled visitor
// (network hiccup, ad/content blocker, CDN error), buildFlow() never runs
// and the attribute never gets set: confirmed live that Home's entire main
// content then stays invisible forever, with zero buy CTA visible, and no
// existing test caught it (test-home-fallback-cls-contract.py only pins the
// CSS mechanics, not what happens when the enhancing script never arrives).
//
// assets/v1-shell.js now schedules a 5s safety-net timeout that reveals the
// fallback if buildFlow() hasn't finished by then. This checks both real
// failure modes actually recover, AND that a healthy load never triggers it
// (which would reintroduce the pre-JS-flash CLS regression the hide rule
// exists to prevent -- see test-home-fallback-cls-contract.py).
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

async function homeState(page) {
  return page.evaluate(() => {
    const root = document.documentElement;
    const river = document.querySelector('.river-grid');
    const yale = document.querySelector('.yale-home-issue');
    return {
      homeEditorialV3Attr: root.dataset.homeEditorialV3 || null,
      riverVisibility: river ? getComputedStyle(river).visibility : null,
      yaleHeroExists: !!yale,
    };
  });
}

try {
  // 1. Healthy load: buildFlow() succeeds well within the 5s safety-net
  // window, so the fallback timeout must never need to fire.
  {
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.goto(`${ORIGIN}/`, { waitUntil: 'load' });
    await page.waitForTimeout(1500);
    const state = await homeState(page);
    assert.equal(state.homeEditorialV3Attr, 'true', 'healthy load: buildFlow() should complete well before the 5s safety net');
    assert.equal(state.yaleHeroExists, true, 'healthy load: dynamic Yale hero should be built');
    await context.close();
  }

  // 2. editorial-public-facts.mjs blocked: the static `import` fails, so the
  // whole v1-home-editorial-v3.js module never evaluates and buildFlow()
  // never runs -- exactly the bug that produced live href="null" buy links.
  {
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.route('**/assets/editorial-public-facts.mjs*', (route) => route.abort());
    await page.goto(`${ORIGIN}/`, { waitUntil: 'load' });
    await page.waitForTimeout(1500);
    const beforeTimeout = await homeState(page);
    assert.equal(beforeTimeout.riverVisibility, 'hidden', 'editorial-public-facts.mjs blocked: fallback must still be hidden before the safety net fires (no premature flash)');
    await page.waitForTimeout(5000);
    const afterTimeout = await homeState(page);
    assert.equal(afterTimeout.riverVisibility, 'visible', 'editorial-public-facts.mjs blocked: safety net must reveal the static fallback after 5s so Home is never permanently blank');
    await context.close();
  }

  // 3. v1-home-editorial-v3.js itself blocked entirely (network/CDN failure,
  // not just its data import) -- same recovery must apply.
  {
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.route('**/assets/v1-home-editorial-v3.js*', (route) => route.abort());
    await page.goto(`${ORIGIN}/`, { waitUntil: 'load' });
    await page.waitForTimeout(6000);
    const state = await homeState(page);
    assert.equal(state.riverVisibility, 'visible', 'v1-home-editorial-v3.js blocked: safety net must reveal the static fallback after 5s');
    await context.close();
  }
} finally {
  await browser.close();
  server.close();
}

console.log('home-editorial-fallback-recovery: OK');
