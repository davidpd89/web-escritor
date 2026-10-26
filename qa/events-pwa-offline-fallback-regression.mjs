import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const browser = await chromium.launch({headless:true});
const context = await browser.newContext({serviceWorkers:'allow'});
try {
  const page = await context.newPage();
  await page.goto(BASE + '/eventos.html', {waitUntil:'domcontentloaded'});
  await page.evaluate(async () => {
    await navigator.serviceWorker.register('/service-worker.js');
    await navigator.serviceWorker.ready;
  });
  await page.reload({waitUntil:'domcontentloaded'});
  await page.waitForFunction(() => Boolean(navigator.serviceWorker.controller));
  const target = '/ferias.html';
  const cached = await page.evaluate(async route => {
    const keys = await caches.keys();
    for (const key of keys) {
      const cache = await caches.open(key);
      if (await cache.match(route)) return true;
    }
    return false;
  }, target);
  assert.equal(cached, false, `${target}: fixture ya está almacenado; no verifica fallback`);
  await context.setOffline(true);
  const response = await page.goto(BASE + target, {waitUntil:'domcontentloaded'});
  assert.ok(response, `${target}: error de navegación sin fallback`);
  const heading = await page.locator('h1').innerText();
  assert.match(heading, /red|conexión/i, `${target}: no aparece el mensaje offline: ${heading}`);
  const retry = page.locator('[data-retry]');
  assert.ok(await retry.isVisible(), `${target}: falta acción visible de reintento`);
  assert.ok(await retry.isEnabled(), `${target}: reintento deshabilitado`);
  assert.ok(await page.locator('[role="status"]').count(), `${target}: falta información de estado accesible`);
} finally {
  await context.close();
  await browser.close();
}
console.log('PASS PWA: recuperación offline de página no visitada');