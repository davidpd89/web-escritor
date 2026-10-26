import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = (process.env.SITE_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ serviceWorkers: 'allow', viewport: { width: 375, height: 812 } });
try {
  const page = await context.newPage();
  const response = await page.goto(`${base}/`, { waitUntil: 'domcontentloaded' });
  assert.equal(response?.status(), 200, '/: página inicial inaccesible');
  await page.evaluate(async () => {
    const registration = await navigator.serviceWorker.register('/service-worker.js');
    await navigator.serviceWorker.ready;
    if (!navigator.serviceWorker.controller) {
      await new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error('Service worker no tomó control')), 15000);
        navigator.serviceWorker.addEventListener('controllerchange', () => { clearTimeout(timer); resolve(); }, { once: true });
      });
    }
    if (!registration.active) throw new Error('Service worker sin activar');
  });
  await context.setOffline(true);
  await page.goto(`${base}/cuaderno/`, { waitUntil: 'domcontentloaded' });
  await page.locator('#offline-title').waitFor({ state: 'visible' });
  const state = await page.evaluate(() => {
    const title = document.querySelector('#offline-title');
    const retry = document.querySelector('[data-retry]');
    const card = document.querySelector('.offline-card');
    const rect = card.getBoundingClientRect();
    return {
      title: title?.textContent.trim(),
      titleVisibility: getComputedStyle(title).visibility,
      retryVisible: !!retry && getComputedStyle(retry).display !== 'none',
      retryHeight: retry?.getBoundingClientRect().height || 0,
      cardLeft: rect.left,
      cardRight: rect.right,
      viewport: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth
    };
  });
  assert.match(state.title, /página|red/i, '/cuaderno/ offline: título de recuperación ausente');
  assert.equal(state.titleVisibility, 'visible', '/cuaderno/ offline: título oculto');
  assert.ok(state.retryVisible && state.retryHeight >= 44, `/cuaderno/ offline: reintento no utilizable, altura=${state.retryHeight}`);
  assert.ok(state.cardLeft >= -1 && state.cardRight <= state.viewport + 1, `/cuaderno/ offline: tarjeta recortada ${JSON.stringify(state)}`);
  assert.ok(state.scrollWidth <= state.viewport + 1, `/cuaderno/ offline: desbordamiento ${state.scrollWidth}/${state.viewport}`);
} finally {
  await context.close();
  await browser.close();
}
console.log('PASS offline service worker visual recovery');