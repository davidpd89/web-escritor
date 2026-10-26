import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const browser = await chromium.launch({headless:true});
const context = await browser.newContext({serviceWorkers:'allow'});
try {
  const page = await context.newPage();
  await page.goto(BASE + '/eventos.html', {waitUntil:'domcontentloaded'});
  const registration = await page.evaluate(async () => {
    if (!('serviceWorker' in navigator)) return false;
    await navigator.serviceWorker.register('/service-worker.js');
    await navigator.serviceWorker.ready;
    return true;
  });
  assert.ok(registration, '/eventos.html: service worker no disponible');
  await page.reload({waitUntil:'domcontentloaded'});
  await page.waitForFunction(() => Boolean(navigator.serviceWorker.controller));
  for (const [route, heading] of [['/eventos.html', 'Eventos'], ['/ferias.html', 'Ferias del libro']]) {
    const response = await page.goto(BASE + route, {waitUntil:'domcontentloaded'});
    assert.ok(response?.ok(), `${route}: no se pudo visitar online`);
    assert.ok((await page.locator('h1').innerText()).includes(heading), `${route}: contenido online inesperado`);
  }
  await context.setOffline(true);
  for (const [route, heading] of [['/eventos.html', 'Eventos'], ['/ferias.html', 'Ferias del libro']]) {
    const response = await page.goto(BASE + route, {waitUntil:'domcontentloaded'});
    assert.ok(response?.ok(), `${route}: navegación offline no recuperada`);
    const title = await page.locator('h1').innerText();
    assert.ok(title.includes(heading), `${route}: caché devuelve otra página: ${title}`);
    assert.ok(await page.locator('main').count(), `${route}: contenido principal perdido offline`);
  }
} finally {
  await context.close();
  await browser.close();
}
console.log('PASS Eventos/Ferias: páginas visitadas recuperables offline');