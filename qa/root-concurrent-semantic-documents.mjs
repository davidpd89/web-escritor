import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const ROUTES = ['/', '/404.html', '/offline.html'];
const browser = await chromium.launch({ headless: true });

try {
  const context = await browser.newContext({ serviceWorkers: 'block', reducedMotion: 'reduce' });
  await context.route('**/*', route => new URL(route.request().url()).origin === ORIGIN ? route.continue() : route.abort());
  const pages = await Promise.all(Array.from({ length: 9 }, () => context.newPage()));
  await Promise.all(pages.map(async (page, index) => {
    const route = ROUTES[index % ROUTES.length];
    const response = await page.goto(ORIGIN + route, { waitUntil: 'domcontentloaded', timeout: 20000 });
    assert.ok(response?.ok(), `${route}: HTTP ${response?.status()} en navegación concurrente ${index}`);
    await page.locator('main h1').first().waitFor({ state: 'visible', timeout: 10000 });
    const state = await page.evaluate(() => ({
      main: document.querySelectorAll('main').length,
      headings: [...document.querySelectorAll('main h1')].filter(el => el.getClientRects().length && el.textContent.trim()).length,
      bytes: document.documentElement.outerHTML.length
    }));
    assert.equal(state.main, 1, `${route}: cantidad de landmarks main: ${state.main}`);
    assert.ok(state.headings >= 1, `${route}: ningún H1 visible dentro de main`);
    assert.ok(state.bytes > 500, `${route}: HTML vacío o truncado (${state.bytes} caracteres)`);
  }));
  await context.close();
} finally {
  await browser.close();
}
console.log('root-concurrent-semantic-documents: OK');