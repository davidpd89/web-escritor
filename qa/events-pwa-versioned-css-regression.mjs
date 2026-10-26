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
  await page.reload({waitUntil:'load'});
  await page.waitForFunction(() => Boolean(navigator.serviceWorker.controller));
  const resources = new Map();
  for (const [route, owner] of [['/eventos.html', 'v1-events.css'], ['/ferias.html', 'v1-ferias.css']]) {
    await page.goto(BASE + route, {waitUntil:'load'});
    const styles = await page.locator('link[rel="stylesheet"]').evaluateAll(els => els.map(el => el.href).filter(url => new URL(url).pathname.startsWith('/assets/') && new URL(url).searchParams.has('v')));
    assert.ok(styles.length, `${route}: no se encontraron estilos versionados`);
    assert.ok(styles.some(url => new URL(url).pathname.endsWith('/' + owner)), `${route}: falta CSS propietario ${owner}`);
    for (const url of styles) resources.set(url, route);
  }
  const offlineResults = await page.evaluate(async urls => {
    const keys = await caches.keys();
    const results = [];
    for (const url of urls) {
      let response = null;
      for (const key of keys) {
        response = await (await caches.open(key)).match(url);
        if (response) break;
      }
      results.push({url, ok: Boolean(response?.ok), type: response?.headers.get('content-type') || '', length: response ? (await response.text()).length : 0});
    }
    return results;
  }, [...resources.keys()]);
  for (const item of offlineResults) {
    assert.ok(item.ok, `${resources.get(item.url)}: CSS versionado no almacenado ${item.url}`);
    assert.match(item.type, /text\/css/i, `${resources.get(item.url)}: MIME CSS incorrecto ${item.url}`);
    assert.ok(item.length > 0, `${resources.get(item.url)}: CSS vacío ${item.url}`);
  }
  await context.setOffline(true);
  for (const route of ['/eventos.html', '/ferias.html']) {
    const response = await page.goto(BASE + route, {waitUntil:'load'});
    assert.ok(response?.ok(), `${route}: página no recuperada offline`);
    const styles = await page.evaluate(() => [...document.styleSheets].filter(s => s.href && new URL(s.href).pathname.startsWith('/assets/')).length);
    assert.ok(styles > 0, `${route}: no se recuperan hojas de estilo offline`);
  }
} finally {
  await context.close();
  await browser.close();
}
console.log('PASS Eventos/Ferias: CSS versionado conservado offline');