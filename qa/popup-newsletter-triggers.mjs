import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ROOT = process.cwd();
const MIME = new Map([
  ['.html', 'text/html; charset=utf-8'], ['.css', 'text/css; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'], ['.mjs', 'text/javascript; charset=utf-8'],
  ['.json', 'application/json; charset=utf-8'], ['.xml', 'application/xml; charset=utf-8'],
  ['.txt', 'text/plain; charset=utf-8'], ['.webp', 'image/webp'], ['.png', 'image/png'],
  ['.jpg', 'image/jpeg'], ['.jpeg', 'image/jpeg'], ['.svg', 'image/svg+xml'],
  ['.woff2', 'font/woff2'], ['.ico', 'image/x-icon'],
]);

function resolvePath(pathname) {
  const clean = decodeURIComponent(pathname.split('?')[0]).replace(/^\/+/, '');
  if (!clean) return path.join(ROOT, 'index.html');
  const candidate = pathname.endsWith('/') ? path.join(ROOT, clean, 'index.html') : path.join(ROOT, clean);
  const normalized = path.resolve(candidate);
  return normalized.startsWith(ROOT) ? normalized : null;
}

const page404 = fs.readFileSync(path.join(ROOT, '404.html'));
const server = createServer((req, res) => {
  const url = new URL(req.url, 'http://127.0.0.1');
  const file = resolvePath(url.pathname);
  if (!file || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
    res.writeHead(404, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' });
    res.end(page404);
    return;
  }
  const type = MIME.get(path.extname(file).toLowerCase()) || 'application/octet-stream';
  res.writeHead(200, { 'Content-Type': type, 'Cache-Control': 'no-store' });
  res.end(fs.readFileSync(file));
});
await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const ORIGIN = `http://127.0.0.1:${server.address().port}`;

async function popupVisible(page) {
  return page.locator('#nl-popup-overlay').count().then((n) => n > 0);
}

async function openCuaderno(context) {
  const page = await context.newPage();
  const response = await page.goto(`${ORIGIN}/cuaderno/`, { waitUntil: 'load' });
  assert(response && response.status() < 400, `HTTP ${response?.status()}`);
  await page.waitForTimeout(250);
  return page;
}

const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

try {
  // 1) No 30s fallback timer should be scheduled.
  {
    const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    await context.addInitScript(() => {
      const originalSetTimeout = window.setTimeout.bind(window);
      window.__dpTimeoutDelays = [];
      window.setTimeout = function patchedSetTimeout(fn, delay, ...args) {
        window.__dpTimeoutDelays.push(Number(delay));
        return originalSetTimeout(fn, delay, ...args);
      };
    });
    const page = await openCuaderno(context);
    const delays = await page.evaluate(() => window.__dpTimeoutDelays || []);
    assert(!delays.includes(30000), 'Popup fallback timer (30000ms) must not be registered');
    await context.close();
  }

  // 2) Scroll threshold: must NOT open below 70%, must open at/above 70%.
  {
    const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    const page = await openCuaderno(context);

    await page.evaluate(() => {
      const maxScroll = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
      window.scrollTo(0, Math.floor(maxScroll * 0.65));
    });
    await page.waitForTimeout(200);
    assert.equal(await popupVisible(page), false, 'Popup opened before 70% scroll threshold');

    await page.evaluate(() => {
      const maxScroll = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
      window.scrollTo(0, Math.floor(maxScroll * 0.72));
    });
    await page.waitForTimeout(250);
    assert.equal(await popupVisible(page), true, 'Popup did not open at/above 70% scroll threshold');
    await context.close();
  }

  // 3) Exit-intent must be ignored when hover/pointer-fine media query is false.
  {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true });
    await context.addInitScript(() => {
      const originalMatchMedia = window.matchMedia.bind(window);
      window.matchMedia = (query) => {
        if (query === '(hover: hover) and (pointer: fine)') {
          return {
            media: query,
            matches: false,
            onchange: null,
            addListener() {},
            removeListener() {},
            addEventListener() {},
            removeEventListener() {},
            dispatchEvent() { return false; },
          };
        }
        return originalMatchMedia(query);
      };
    });
    const page = await openCuaderno(context);

    await page.evaluate(() => {
      document.dispatchEvent(new MouseEvent('mouseleave', { bubbles: true, clientY: 0 }));
    });
    await page.waitForTimeout(200);
    assert.equal(await popupVisible(page), false, 'Exit-intent opened popup even when pointer is not fine-hover');
    await context.close();
  }

  // 4) Exit-intent should still work when the media query is true.
  {
    const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    await context.addInitScript(() => {
      const originalMatchMedia = window.matchMedia.bind(window);
      window.matchMedia = (query) => {
        if (query === '(hover: hover) and (pointer: fine)') {
          return {
            media: query,
            matches: true,
            onchange: null,
            addListener() {},
            removeListener() {},
            addEventListener() {},
            removeEventListener() {},
            dispatchEvent() { return false; },
          };
        }
        return originalMatchMedia(query);
      };
    });
    const page = await openCuaderno(context);

    await page.evaluate(() => {
      document.dispatchEvent(new MouseEvent('mouseleave', { bubbles: true, clientY: 0 }));
    });
    await page.waitForTimeout(250);
    assert.equal(await popupVisible(page), true, 'Exit-intent did not open popup when pointer is fine-hover');
    await context.close();
  }

  console.log('popup-newsletter-triggers: PASS');
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
