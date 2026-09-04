// Buy/Comprar CTA contract for Las manecillas del recuerdo, checked AFTER
// JS execution (not static source analysis) across every real surface that
// carries one: header (sitewide), Home hero + Home rail (both dynamically
// built by assets/v1-home-editorial-v3.js), the book page, fragmentos, and
// the Kindle landing page.
//
// This exists because two real regressions shipped invisibly to static
// analysis: (1) Home's dynamically-created Comprar links were missing
// rel="sponsored nofollow" and the aria-label disclosure because their
// amzn.to host wasn't recognized by the affiliate-detection logic, and
// (2) those same links' clicks fired zero analytics events because
// script.js wired its click tracker via a one-time querySelectorAll() that
// ran before the async module had built the DOM. Both were only visible by
// actually loading the page, letting its JS run, and clicking the real
// rendered link -- which is what this script does.
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const CANONICAL_BUY_URL = JSON.parse(fs.readFileSync(path.join(ROOT, 'editorial-facts.json'), 'utf8'))
  .books.lasManecillasDelRecuerdo.purchaseUrl;

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

async function withGoatcounterSpy(page) {
  await page.route(/gc\.zgo\.at/, (route) => route.abort());
  await page.route(/metricool\.com/, (route) => route.abort());
  await page.route(/amzn\.to|amazon\.es/, (route) => route.abort());
  await page.addInitScript(() => {
    window.__gcCalls = [];
    window.goatcounter = { count: (payload) => window.__gcCalls.push(payload) };
  });
}

async function checkSurface(page, { route, selector, label, waitMs = 800 }) {
  await page.goto(`${ORIGIN}${route}`, { waitUntil: 'load' });
  await page.waitForTimeout(waitMs);
  const links = page.locator(selector);
  const count = await links.count();
  assert.ok(count > 0, `${label}: no buy CTA found matching ${selector} on ${route}`);

  for (let i = 0; i < count; i += 1) {
    const link = links.nth(i);
    const [href, target, rel, ariaLabel, text, visible] = await Promise.all([
      link.getAttribute('href'),
      link.getAttribute('target'),
      link.getAttribute('rel'),
      link.getAttribute('aria-label'),
      link.textContent(),
      link.isVisible(),
    ]);
    const accessibleName = (ariaLabel || text || '').trim();
    assert.equal(href, CANONICAL_BUY_URL, `${label} #${i}: href is ${href}, expected ${CANONICAL_BUY_URL}`);
    assert.equal(target, '_blank', `${label} #${i}: target must be _blank`);
    assert.match(rel || '', /\bsponsored\b/, `${label} #${i}: rel missing "sponsored" (rel=${rel})`);
    assert.match(rel || '', /\bnofollow\b/, `${label} #${i}: rel missing "nofollow" (rel=${rel})`);
    assert.match(rel || '', /\bnoopener\b/, `${label} #${i}: rel missing "noopener" (rel=${rel})`);
    assert.ok(accessibleName.length > 0, `${label} #${i}: no accessible name (text or aria-label)`);
    assert.doesNotMatch(text || '', /afiliad/i, `${label} #${i}: visible text must not say "Afiliado" (text=${text})`);
    assert.ok(visible, `${label} #${i}: CTA is not visible/clickable`);
  }

  // Exactly one analytics event per click, on the first matching CTA.
  await withGoatcounterSpy(page);
  await page.goto(`${ORIGIN}${route}`, { waitUntil: 'load' });
  await page.waitForTimeout(waitMs);
  await page.locator(selector).first().click({ noWaitAfter: true }).catch(() => {});
  await page.waitForTimeout(300);
  const calls = await page.evaluate(() => window.__gcCalls);
  const buyEvents = calls.filter((c) => c.path === 'comprar-amazon');
  assert.equal(buyEvents.length, 1, `${label}: expected exactly 1 comprar-amazon event, got ${buyEvents.length}`);
}

try {
  const context = await browser.newContext();
  const page = await context.newPage();

  await checkSurface(page, {
    route: '/las-manecillas-del-recuerdo/',
    selector: '.site-header a.header-buy',
    label: 'header (sitewide)',
  });

  await checkSurface(page, {
    route: '/',
    selector: '.yale-lead__actions a[href*="amzn.to"], .yale-rail a[href*="amzn.to"]',
    label: 'Home hero + rail (dynamic)',
  });

  await checkSurface(page, {
    route: '/las-manecillas-del-recuerdo/',
    selector: '.book-actions a[href*="amzn.to"]',
    label: 'ficha (book page hero)',
  });

  await checkSurface(page, {
    route: '/las-manecillas-del-recuerdo/fragmentos/',
    selector: '#cta-final a[href*="amzn.to"]',
    label: 'fragmentos (cta-final)',
  });

  await checkSurface(page, {
    route: '/las-manecillas-del-recuerdo/kindle/',
    selector: '.book-actions a[href*="amzn.to"]',
    label: 'Kindle landing (hero)',
  });

  await context.close();
} finally {
  await browser.close();
  server.close();
}

console.log('manecillas-buy-cta-contract: OK');
