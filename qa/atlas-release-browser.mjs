// Future integration browser QA. NOT imported into existing workflows.
// Requires real approved Atlas pages, facet JSON shards and published shell.
// Usage after development: node qa/atlas-release-browser.mjs --root ./site-build
import assert from 'node:assert/strict';
import { chromium, firefox, webkit } from 'playwright';
import { createServer } from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const idx = process.argv.indexOf('--root');
if (idx < 0 || !process.argv[idx + 1]) {
  throw new Error('Use --root <built static site> after atlas implementation');
}
const ROOT = path.resolve(process.argv[idx + 1]);
const MIME = new Map(Object.entries({
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript',
  '.mjs': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json; charset=utf-8', '.xml': 'application/xml',
  '.svg': 'image/svg+xml', '.webp': 'image/webp', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.woff2': 'font/woff2'
}));
const server = createServer((req, res) => {
  let filename;
  try {
    const pathname = decodeURIComponent(new URL(req.url, 'http://127.0.0.1').pathname);
    filename = path.resolve(ROOT, '.' + pathname, pathname.endsWith('/') ? 'index.html' : '');
    if (!filename.startsWith(ROOT + path.sep)) throw new Error('traversal');
  } catch {
    res.writeHead(400); res.end(); return;
  }
  if (!fs.existsSync(filename) || !fs.statSync(filename).isFile()) {
    res.writeHead(404); res.end('Not Found'); return;
  }
  res.writeHead(200, { 'Content-Type': MIME.get(path.extname(filename)) || 'application/octet-stream' });
  res.end(fs.readFileSync(filename));
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const ORIGIN = 'http://127.0.0.1:' + server.address().port;
const manifestPath = path.join(ROOT, 'atlas-release-manifest.json');
if (!fs.existsSync(manifestPath)) {
  server.close();
  throw new Error('Atlas release manifest missing: ' + manifestPath);
}
const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
const routes = manifest.routes || [];
const hub = routes.find(r => r.kind === 'hub')?.url;
const place = routes.find(r => r.kind === 'place')?.url;
const destination = routes.find(r => r.kind === 'destination')?.url;
assert(hub && place && destination, 'Need hub + approved destination + place fixture');

const engines = process.env.ATLAS_BROWSERS
  ? process.env.ATLAS_BROWSERS.split(',').map(s => s.trim())
  : ['chromium', 'firefox', 'webkit'];
const browsers = { chromium, firefox, webkit };
const sizes = [
  { name: 'mobile', viewport: { width: 390, height: 844 } },
  { name: 'desktop', viewport: { width: 1440, height: 900 } }
];

try {
  for (const name of engines) {
    assert(browsers[name], 'Unknown browser ' + name);
    const browser = await browsers[name].launch({ headless: true });
    try {
      for (const size of sizes) {
        const context = await browser.newContext({ ...size });
        const page = await context.newPage();
        const pageErrors = [];
        const thirdParty = [];
        const mapRequests = [];
        page.on('pageerror', error => pageErrors.push(error.message));
        await page.route('**/*', route => {
          const url = route.request().url();
          if (!url.startsWith(ORIGIN)) {
            thirdParty.push(url);
            return route.abort();
          }
          if (/\/tiles\/|maplibre|leaflet|supercluster/i.test(url)) mapRequests.push(url);
          return route.continue();
        });
        for (const routePath of [hub, destination, place]) {
          const response = await page.goto(ORIGIN + routePath, { waitUntil: 'domcontentloaded' });
          assert.equal(response.status(), 200, name + '/' + size.name + routePath + ' HTTP');
          assert.equal(await page.locator('main h1').count(), 1, 'Single h1');
          assert(await page.locator('a[href]').count() > 0, 'Page navigable as HTML');
          const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
          assert.equal(overflow, false, routePath + ' horizontal overflow');
        }
        assert.equal(mapRequests.length, 0, 'Map SDK/tiles should not load during base navigation');
        assert.equal(pageErrors.length, 0, 'JavaScript errors: ' + pageErrors.join(', '));
        // First-release expectation: HTML must remain useful with JS disabled.
        const noJsContext = await browser.newContext({ ...size, javaScriptEnabled: false });
        try {
          const noJsPage = await noJsContext.newPage();
          await noJsPage.goto(ORIGIN + destination, { waitUntil: 'domcontentloaded' });
          assert(await noJsPage.locator('main a[href]').count() > 0,
                 'Destination no-JS links');
        } finally {
          await noJsContext.close();
        }

        // Interactive facet behaviour will be gated only after #672 is installed
        // into the real site shell. Never hide absent filters behind a skip.
        await page.goto(ORIGIN + hub, { waitUntil: 'domcontentloaded' });
        const controls = page.locator('[data-atlas-explore]');
        assert.equal(await controls.count(), 1, 'Atlas facet UI not yet integrated');
        const country = page.locator('[data-atlas-country]');
        assert.equal(await country.count(), 1, 'Country combobox missing');
        await country.focus();
        await page.waitForFunction(() =>
          document.querySelector('[data-atlas-country]')?.options.length > 1,
          null, { timeout: 8000 });
        const countryValues = await country.locator('option').evaluateAll(
          els => els.map(el => el.value).filter(Boolean)
        );
        await country.selectOption(countryValues[0]);
        const city = page.locator('[data-atlas-destination]');
        await page.waitForFunction(() =>
          document.querySelector('[data-atlas-destination]')?.options.length > 1,
          null, { timeout: 8000 });
        const dests = await city.locator('option').evaluateAll(
          els => els.map(el => el.value).filter(Boolean)
        );
        await city.selectOption(dests[0]);
        await page.locator('[data-atlas-results] a').first().waitFor({ timeout: 8000 });
        assert.equal(pageErrors.length, 0, 'Facet JS errors: ' + pageErrors.join(', '));

        await context.close();
        console.log('Atlas QA: ' + name + '/' + size.name + ' OK');
      }
    } finally {
      await browser.close();
    }
  }
} finally {
  await new Promise(resolve => server.close(resolve));
}
