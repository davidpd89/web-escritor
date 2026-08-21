import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const BASE = process.env.MACHINE_BASE_URL || 'http://127.0.0.1:4173';
const OUT = process.env.MACHINE_ARTIFACT_DIR || 'artifacts/machine-authority';
const route = '/ai/';
const viewports = [
  { name: '320', width: 320, height: 780 },
  { name: '390', width: 390, height: 844 },
  { name: '768', width: 768, height: 1024 },
  { name: '1024', width: 1024, height: 900 },
  { name: '1440', width: 1440, height: 1000 },
  { name: '1728', width: 1728, height: 1050 },
  { name: 'landscape-844x390', width: 844, height: 390 },
];

const failures = [];
const metrics = [];
const fail = (message) => failures.push(message);
const check = (value, message) => { if (!value) fail(message); };

await fs.mkdir(OUT, { recursive: true });
const browser = await chromium.launch({ headless: true });

async function contextFor(viewport, extra = {}) {
  return browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
    reducedMotion: 'reduce',
    ...extra,
  });
}

async function openChecked(context) {
  const page = await context.newPage();
  const errors = [];
  const brokenLocal = [];
  await page.addInitScript(() => {
    window.__machineCLS = 0;
    try {
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (!entry.hadRecentInput) window.__machineCLS += entry.value;
        }
      }).observe({ type: 'layout-shift', buffered: true });
    } catch (_) {}
  });
  page.on('pageerror', (error) => errors.push(`pageerror: ${error.message}`));
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(`console: ${message.text()}`);
  });
  page.on('response', (response) => {
    const url = new URL(response.url());
    if (url.origin === new URL(BASE).origin && response.status() >= 400) {
      brokenLocal.push(`${response.status()} ${url.pathname}`);
    }
  });

  const response = await page.goto(BASE + route, { waitUntil: 'domcontentloaded' });
  check(response && response.ok(), `${route}: HTTP ${response?.status() ?? 'no response'}`);
  await page.waitForTimeout(250);
  const state = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    cls: window.__machineCLS || 0,
    mainText: document.querySelector('main')?.innerText.trim().length || 0,
    h1: document.querySelectorAll('h1').length,
    h2: document.querySelectorAll('h2').length,
    canonical: document.querySelector('link[rel="canonical"]')?.href || '',
    robots: document.querySelector('meta[name="robots"]')?.content || '',
    scripts: [...document.scripts].map((s) => s.type || 'text/javascript'),
  }));
  return { page, errors, brokenLocal, state };
}

for (const viewport of viewports) {
  const context = await contextFor(viewport);
  const { errors, brokenLocal, state } = await openChecked(context);
  check(state.scrollWidth <= state.clientWidth + 1, `${route} @ ${viewport.name}: horizontal overflow ${state.scrollWidth}/${state.clientWidth}`);
  check(state.mainText > 2000, `${route} @ ${viewport.name}: authority content unexpectedly short`);
  check(state.h1 === 1 && state.h2 >= 5, `${route} @ ${viewport.name}: heading structure invalid (${state.h1} h1, ${state.h2} h2)`);
  check(state.canonical === 'https://davidportodiaz.com/ai/', `${route}: canonical mismatch`);
  check(state.robots.includes('index') && state.robots.includes('follow'), `${route}: robots meta not index/follow`);
  check(state.scripts.every((type) => type === 'application/ld+json'), `${route}: runtime script introduced`);
  check(errors.length === 0, `${route} @ ${viewport.name}: ${errors.join(' | ')}`);
  check(brokenLocal.length === 0, `${route} @ ${viewport.name}: broken local assets ${[...new Set(brokenLocal)].join(', ')}`);
  check(state.cls <= 0.1, `${route} @ ${viewport.name}: CLS ${state.cls.toFixed(4)} > 0.1`);
  metrics.push({ viewport: viewport.name, cls: state.cls, overflow: state.scrollWidth - state.clientWidth });
  await context.close();
}

{
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, javaScriptEnabled: false });
  const page = await context.newPage();
  const response = await page.goto(BASE + route, { waitUntil: 'domcontentloaded' });
  check(response && response.ok(), `${route} no-JS: HTTP failure`);
  const state = await page.evaluate(() => ({
    text: document.querySelector('main')?.innerText.trim().length || 0,
    display: getComputedStyle(document.querySelector('main')).display,
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
  }));
  check(state.text > 2000 && state.display !== 'none', `${route} no-JS: authority content unavailable`);
  check(state.overflow <= 1, `${route} no-JS: horizontal overflow ${state.overflow}`);
  await context.close();
}

{
  const context = await contextFor({ width: 390, height: 844 });
  const { page } = await openChecked(context);
  await page.keyboard.press('Tab');
  const skip = page.locator('.skip-link');
  check(await skip.evaluate((el) => el === document.activeElement), 'a11y: first Tab does not focus skip link');
  const skipBox = await skip.boundingBox();
  check(Boolean(skipBox && skipBox.width > 0 && skipBox.height > 0), 'a11y: skip link not visible on focus');
  await page.keyboard.press('Enter');
  check((await page.evaluate(() => location.hash)) === '#contenido', 'a11y: skip link does not target #contenido');
  await context.close();
}

{
  const context = await contextFor({ width: 390, height: 844 });
  const { page } = await openChecked(context);
  await page.addStyleTag({ content: `*{line-height:1.5 !important;letter-spacing:.12em !important;word-spacing:.16em !important} p{margin-bottom:2em !important}` });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  check(overflow <= 1, `a11y text-spacing: horizontal overflow ${overflow}`);
  await context.close();
}

{
  const context = await contextFor({ width: 390, height: 844 });
  const { page } = await openChecked(context);
  await page.addStyleTag({ content: `html{font-size:200% !important}` });
  const state = await page.evaluate(() => ({
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    text: document.querySelector('main')?.innerText.trim().length || 0,
  }));
  check(state.overflow <= 1, `a11y 200% text zoom: horizontal overflow ${state.overflow}`);
  check(state.text > 2000, 'a11y 200% text zoom: content lost');
  await context.close();
}

for (const [width, height, file] of [
  [1440, 1000, 'ai-1440.png'],
  [390, 844, 'ai-390.png'],
]) {
  const context = await contextFor({ width, height });
  const page = await context.newPage();
  await page.goto(BASE + route, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(250);
  await page.screenshot({ path: path.join(OUT, file), fullPage: true });
  await context.close();
}

await fs.writeFile(path.join(OUT, 'browser-metrics.json'), JSON.stringify({ metrics, failures }, null, 2));
await browser.close();

if (failures.length) {
  console.error('\nMachine authority browser QA failed:');
  for (const message of failures) console.error(`- ${message}`);
  process.exit(1);
}
console.log(`Machine authority browser QA PASS (${viewports.length} artboards + no-JS/a11y fixtures).`);
