import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
try {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  await context.route('**/*', r => new URL(r.request().url()).origin === new URL(BASE).origin ? r.continue() : r.abort());
  await context.addInitScript(() => localStorage.setItem('nl-popup-ts', String(Date.now())));
  const page = await context.newPage();
  await page.goto(BASE + '/cuaderno/');
  const allowed = await page.evaluate(() => window.DP_SURPRISE_CONTENT.map(x => x.url));
  assert.ok(allowed.length >= 5, 'Lista demasiado pequeña para comprobar exclusiones');
  const visited = [];
  for (let i = 0; i < 5; i++) {
    const current = new URL(page.url()).pathname;
    assert.equal(current, '/cuaderno/');
    await page.locator('[data-surprise-me]').click();
    await page.waitForURL(url => url.pathname !== '/cuaderno/');
    const target = new URL(page.url()).pathname;
    assert.ok(allowed.includes(target), `Destino fuera de allowlist: ${target}`);
    assert.notEqual(target, current);
    assert.ok(!visited.slice(-3).includes(target), `Repetición prematura: ${target}`);
    visited.push(target);
    await page.goBack({ waitUntil: 'domcontentloaded' });
  }
  const recent = await page.evaluate(() => JSON.parse(sessionStorage.getItem('dp_surprise_recent_v1') || '[]'));
  assert.deepEqual(recent, visited.slice(-3).reverse());
  await context.close();
  console.log('PASS cuaderno surprise navigation stateful');
} finally { await browser.close(); }
