// Sitewide zero-console-errors crawl (2026-09-16 audit, GPT batch item #1).
// Existing coverage check first: ~40 qa/*.mjs suites already assert
// `errors.length === 0` (console.error/pageerror) for the SPECIFIC pages
// each one exercises, and cross-engine-smoke.mjs does the same across 3
// browser engines but only for 10 representative routes. None of them visit
// every published page. This suite closes that gap by walking the actual
// build output (.preview-dist, the same allowlist-first artifact GitHub
// Pages serves) rather than raw repo source -- source includes deprecated/
// gated pages (see data/content-registry.json GATED_REGISTRY_STATUS) that
// are never supposed to be reachable, and asserting they're error-free would
// be meaningless since real visitors can't load them.
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const DIST = process.env.SITEWIDE_DIST || path.join(ROOT, '.preview-dist-sitewide-qa');
const KEEP_DIST = process.env.SITEWIDE_KEEP_DIST === '1';

if (!process.env.SITEWIDE_SKIP_BUILD) {
  execFileSync('python3', ['scripts/build-public-dist.py', '--out', DIST], { cwd: ROOT, stdio: 'inherit' });
}

function collectHtmlFiles(dir, base = dir) {
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...collectHtmlFiles(full, base));
    else if (entry.name.endsWith('.html')) out.push(path.relative(base, full).replaceAll('\\', '/'));
  }
  return out;
}

function toRoute(relHtmlPath) {
  if (relHtmlPath === 'index.html') return '/';
  if (relHtmlPath.endsWith('/index.html')) return '/' + relHtmlPath.slice(0, -'index.html'.length);
  return '/' + relHtmlPath;
}

const routes = collectHtmlFiles(DIST).map(toRoute).sort();
assert(routes.length > 50, `expected the full public site (>50 pages), found ${routes.length} -- build likely broken`);

const MIME = new Map([
  ['.html', 'text/html; charset=utf-8'], ['.css', 'text/css; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'], ['.mjs', 'text/javascript; charset=utf-8'],
  ['.json', 'application/json; charset=utf-8'], ['.xml', 'application/xml; charset=utf-8'],
  ['.txt', 'text/plain; charset=utf-8'], ['.webp', 'image/webp'], ['.png', 'image/png'],
  ['.jpg', 'image/jpeg'], ['.jpeg', 'image/jpeg'], ['.svg', 'image/svg+xml'],
  ['.woff2', 'font/woff2'], ['.woff', 'font/woff'], ['.ico', 'image/x-icon'],
  ['.ics', 'text/calendar'], ['.webmanifest', 'application/manifest+json'],
]);
const server = createServer((req, res) => {
  const url = new URL(req.url, 'http://127.0.0.1');
  let clean = decodeURIComponent(url.pathname.split('?')[0]).replace(/^\/+/, '');
  if (clean === '' || clean.endsWith('/')) clean += 'index.html';
  const file = path.join(DIST, clean);
  if (!file.startsWith(DIST) || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
    const notFound = path.join(DIST, '404.html');
    if (fs.existsSync(notFound)) {
      res.writeHead(404, { 'Content-Type': 'text/html; charset=utf-8' });
      res.end(fs.readFileSync(notFound));
    } else {
      res.writeHead(404);
      res.end();
    }
    return;
  }
  res.writeHead(200, { 'Content-Type': MIME.get(path.extname(file).toLowerCase()) || 'application/octet-stream' });
  res.end(fs.readFileSync(file));
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const ORIGIN = `http://127.0.0.1:${server.address().port}`;

const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
const findings = [];

try {
  for (const route of routes) {
    const context = await browser.newContext();
    const page = await context.newPage();
    const issues = [];

    page.on('console', (msg) => {
      const type = msg.type();
      if (type === 'error' || type === 'warning') {
        issues.push({ kind: `console.${type === 'warning' ? 'warn' : 'error'}`, text: msg.text() });
      }
    });
    page.on('pageerror', (error) => issues.push({ kind: 'pageerror', text: error.message }));
    await page.exposeFunction('__reportUnhandledRejection', (reason) => {
      issues.push({ kind: 'unhandledrejection', text: String(reason) });
    });
    await page.addInitScript(() => {
      window.addEventListener('unhandledrejection', (e) => {
        window.__reportUnhandledRejection(e.reason && e.reason.message ? e.reason.message : String(e.reason));
      });
    });
    page.on('response', (response) => {
      const status = response.status();
      if (status < 400) return;
      const reqUrl = response.url();
      const isSameOrigin = reqUrl.startsWith(ORIGIN);
      issues.push({ kind: isSameOrigin ? 'same-origin-http-error' : 'cross-origin-http-error', text: `${status} ${reqUrl}` });
    });
    page.on('requestfailed', (request) => {
      const failure = request.failure();
      const text = failure ? failure.errorText : 'unknown';
      // CORS failures surface here (net::ERR_FAILED with no response), not as a 'response' event.
      if (/cors|blocked/i.test(text)) issues.push({ kind: 'cors-error', text: `${text} ${request.url()}` });
    });

    try {
      const response = await page.goto(ORIGIN + route, { waitUntil: 'load', timeout: 20000 });
      if (!response || !response.ok()) {
        issues.push({ kind: 'navigation', text: `HTTP ${response ? response.status() : 'no response'}` });
      }
    } catch (err) {
      issues.push({ kind: 'navigation', text: err.message });
    }
    await page.waitForTimeout(300);

    if (issues.length) findings.push({ route, issues });
    await context.close();
  }
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
  if (!KEEP_DIST) {
    fs.rmSync(DIST, { recursive: true, force: true });
    fs.rmSync(`${DIST}-manifest.json`, { force: true });
  }
}

if (findings.length) {
  console.error(`\nSitewide console-error audit failed: ${findings.length}/${routes.length} page(s) with issues.\n`);
  for (const { route, issues } of findings) {
    console.error(`- ${route}`);
    for (const issue of issues) console.error(`    [${issue.kind}] ${issue.text}`);
  }
  process.exit(1);
}
console.log(`Sitewide console-error audit: PASS (${routes.length} published pages, zero console/network errors).`);
