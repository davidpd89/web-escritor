import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = (process.env.SITE_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ serviceWorkers: 'allow', viewport: { width: 390, height: 844 } });
try {
  const page = await context.newPage();
  await page.goto(`${base}/`, { waitUntil: 'load' });
  await page.locator('body').waitFor({ state: 'visible' });
  const stylesheets = await page.evaluate(() => [...document.querySelectorAll('link[rel~=stylesheet]')].map(x => x.href).filter(x => new URL(x).origin === location.origin));
  assert.ok(stylesheets.length > 0, '/: ninguna hoja CSS local descubierta');
  for (const url of stylesheets) {
    const response = await page.request.get(url);
    assert.equal(response.status(), 200, `/: CSS ${url} devolvió HTTP ${response.status()}`);
    assert.match(response.headers()['content-type'] || '', /text\/css/i, `/: CSS ${url} tiene MIME incorrecto`);
  }
  const snapshot = () => page.evaluate(() => {
    const selectors = ['body', 'h1', 'main', 'header'];
    return selectors.filter(selector => document.querySelector(selector)).map(selector => {
      const element = document.querySelector(selector);
      const style = getComputedStyle(element);
      return { selector, color: style.color, backgroundColor: style.backgroundColor, fontFamily: style.fontFamily, fontSize: style.fontSize, lineHeight: style.lineHeight, display: style.display };
    });
  });
  const initial = await snapshot();
  await page.evaluate(async () => {
    await navigator.serviceWorker.register('/service-worker.js');
    await navigator.serviceWorker.ready;
    if (!navigator.serviceWorker.controller) {
      await new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error('Service worker sin control')), 15000);
        navigator.serviceWorker.addEventListener('controllerchange', () => { clearTimeout(timer); resolve(); }, { once: true });
      });
    }
  });
  await page.reload({ waitUntil: 'load' });
  const after = await snapshot();
  assert.deepEqual(after, initial, `/: estilos computados distintos tras activar service worker. Antes=${JSON.stringify(initial)}, después=${JSON.stringify(after)}`);
} finally {
  await context.close();
  await browser.close();
}
console.log('PASS PWA CSS computed style parity');