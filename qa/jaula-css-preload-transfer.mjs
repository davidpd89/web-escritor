import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const ROUTE = '/donde-empieza-la-jaula/';
const browser = await chromium.launch({ headless: true });

try {
  const context = await browser.newContext();
  const page = await context.newPage();
  const client = await context.newCDPSession(page);
  await client.send('Network.enable');
  await client.send('Network.setCacheDisabled', { cacheDisabled: true });

  const transfers = new Map();
  client.on('Network.responseReceived', event => {
    if (event.type !== 'Stylesheet') return;
    const url = event.response.url;
    if (!url.startsWith(`${ORIGIN}/assets/`)) return;
    const key = new URL(url).pathname + new URL(url).search;
    transfers.set(key, (transfers.get(key) || 0) + 1);
  });

  const response = await page.goto(`${ORIGIN}${ROUTE}`, { waitUntil: 'networkidle' });
  assert.equal(response?.status(), 200, `${ROUTE}: HTTP inesperado`);

  const preloads = await page.locator('link[rel="preload"][as="style"]').evaluateAll(elements => elements.map(element => new URL(element.href).pathname + new URL(element.href).search));
  assert.ok(preloads.length > 0, `${ROUTE}: no se encontraron precargas CSS`);

  for (const resource of preloads) {
    const count = transfers.get(resource) || 0;
    assert.ok(count <= 1, `${ROUTE}: ${resource} produjo ${count} respuestas CSS; máximo permitido: 1`);
  }

  await context.close();
} finally {
  await browser.close();
}

console.log('OK: precargas CSS sin respuestas duplicadas');