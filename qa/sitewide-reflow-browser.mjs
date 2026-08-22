import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const ROOT = process.cwd();
const OUT_DIR = process.env.QA_OUT || 'qa-artifacts';
const REPORT_PATH = path.join(OUT_DIR, 'sitewide-reflow-report.json');
const VIEWPORTS = [
  { width: 390, height: 900 },
  { width: 768, height: 1000 },
];

const IGNORE_DIRS = new Set([
  '.git',
  '.github',
  'node_modules',
  'qa-artifacts',
  'docs',
  'lab',
  '_tools',
  '_reddit',
]);

function normalizeRoute(value) {
  if (!value) return null;
  let route = value.trim();
  if (!route) return null;
  if (/^https?:\/\//i.test(route)) {
    try {
      route = new URL(route).pathname;
    } catch {
      return null;
    }
  }
  if (!route.startsWith('/')) route = `/${route}`;
  route = route.replace(/\/index\.html$/i, '/');
  route = route.replace(/\/+/g, '/');
  if (route !== '/' && route.endsWith('//')) route = route.slice(0, -1);
  return route;
}

function routeFromHtmlPath(filePath) {
  const rel = path.relative(ROOT, filePath).replace(/\\/g, '/');
  if (rel === 'index.html') return '/';
  if (rel.endsWith('/index.html')) return `/${rel.slice(0, -'index.html'.length)}`;
  return `/${rel}`;
}

function walkHtmlFiles(dirPath, out) {
  const items = fs.readdirSync(dirPath, { withFileTypes: true });
  for (const item of items) {
    if (item.name.startsWith('.')) continue;
    const full = path.join(dirPath, item.name);
    if (item.isDirectory()) {
      if (IGNORE_DIRS.has(item.name)) continue;
      walkHtmlFiles(full, out);
      continue;
    }
    if (item.isFile() && item.name.endsWith('.html')) out.push(full);
  }
}

function collectRoutes() {
  const routes = new Set();

  const sitemap = path.join(ROOT, 'sitemap.xml');
  if (fs.existsSync(sitemap)) {
    const xml = fs.readFileSync(sitemap, 'utf8');
    const matches = [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)];
    for (const match of matches) {
      const route = normalizeRoute(match[1]);
      if (route) routes.add(route);
    }
  }

  const registryPath = path.join(ROOT, 'data', 'content-registry.json');
  if (fs.existsSync(registryPath)) {
    const payload = JSON.parse(fs.readFileSync(registryPath, 'utf8'));
    for (const item of payload?.routes || []) {
      if (!item || item.status === 'draft') continue;
      if (item.url) {
        const route = normalizeRoute(item.url);
        if (route) routes.add(route);
      }
      if (typeof item.sourceFile === 'string' && item.sourceFile.endsWith('.html')) {
        const route = normalizeRoute(routeFromHtmlPath(path.join(ROOT, item.sourceFile)));
        if (route) routes.add(route);
      }
    }
  }

  const htmlFiles = [];
  walkHtmlFiles(ROOT, htmlFiles);
  for (const filePath of htmlFiles) {
    const route = normalizeRoute(routeFromHtmlPath(filePath));
    if (route) routes.add(route);
  }

  // Explicit machine/readability surfaces that are part of release smoke.
  routes.add('/ai/');
  routes.add('/privacidad.html');
  routes.add('/aviso-legal.html');
  routes.add('/asistente/');

  return [...routes].sort((a, b) => a.localeCompare(b));
}

async function applyInspectorStyles(context, page, cssText) {
  const cdp = await context.newCDPSession(page);
  await cdp.send('Page.enable');
  await cdp.send('DOM.enable');
  await cdp.send('CSS.enable');
  const { frameTree } = await cdp.send('Page.getFrameTree');
  const { styleSheetId } = await cdp.send('CSS.createStyleSheet', { frameId: frameTree.frame.id });
  await cdp.send('CSS.setStyleSheetText', { styleSheetId, text: cssText });
}

async function settle(page) {
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
}

async function measureOverflow(page) {
  return page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
}

const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH || undefined,
});
await fs.promises.mkdir(OUT_DIR, { recursive: true });

const routes = collectRoutes();
const failures = [];
const checks = [];

for (const route of routes) {
  for (const vp of VIEWPORTS) {
    const context = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      javaScriptEnabled: true,
      reducedMotion: 'reduce',
    });
    const page = await context.newPage();
    const key = `${route}@${vp.width}x${vp.height}`;
    try {
      const response = await page.goto(`${ORIGIN}${route}`, { waitUntil: 'networkidle' });
      assert.ok(response, `${key}: missing response`);
      assert.equal(response.status(), 200, `${key}: expected HTTP 200`);
      await applyInspectorStyles(
        context,
        page,
        '*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}'
      );
      await settle(page);
      await page.evaluate(() => {
        document.documentElement.style.zoom = '2';
      });
      await settle(page);
      const overflow = await measureOverflow(page);
      checks.push({ route, viewport: `${vp.width}x${vp.height}`, overflow });
      if (overflow > 1) {
        failures.push({ route, viewport: `${vp.width}x${vp.height}`, overflow });
      }
    } catch (error) {
      failures.push({ route, viewport: `${vp.width}x${vp.height}`, error: String(error?.message || error) });
    } finally {
      await context.close();
    }
  }
}

await browser.close();

const report = {
  origin: ORIGIN,
  routeCount: routes.length,
  viewportCount: VIEWPORTS.length,
  checks,
  failures,
};
fs.writeFileSync(REPORT_PATH, `${JSON.stringify(report, null, 2)}\n`, 'utf8');

if (failures.length) {
  const lines = failures.slice(0, 30).map(item => {
    if (item.error) return `${item.route} ${item.viewport}: ${item.error}`;
    return `${item.route} ${item.viewport}: overflow ${item.overflow}px`;
  });
  throw new Error(`sitewide reflow failures (${failures.length})\n${lines.join('\n')}`);
}

console.log(`sitewide-reflow-browser: OK (${routes.length} routes, ${VIEWPORTS.length} viewports, ${checks.length} checks)`);
