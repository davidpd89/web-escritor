import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const routes = [
  '/cuaderno/',
  '/cuaderno/que-es-el-portal-fantasy/',
  '/cuaderno/portal-fantasy-vs-fantasia-epica/',
  '/cuaderno/fantasia-juvenil-espanola-portales-magia-coste/',
  '/cuaderno/libros-fantasia-juvenil-espanola-2025-2026/',
  '/cuaderno/worldbuilding-noveris-ciudad-magica/',
  '/cuaderno/feria-libro-madrid-2026-samuel-entre-mundos/',
  '/cuaderno/sistema-de-magia-noveris/'
];

const browser = await chromium.launch({ headless: true });
try {
  const context = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 390, height: 844 } });
  await context.route('**/*', route => new URL(route.request().url()).origin === new URL(BASE).origin ? route.continue() : route.abort());
  for (const route of routes) {
    const page = await context.newPage();
    try {
      const response = await page.goto(BASE + route);
      assert.equal(response.status(), 200, route);
      const dead = await page.evaluate(() => [...document.querySelectorAll('main button, main form')].filter(el => {
        const s = getComputedStyle(el);
        if (s.display === 'none' || s.visibility === 'hidden' || el.hidden || el.inert || el.disabled) return false;
        if (el.matches('button')) return true;
        if (el.matches('form')) return !el.getAttribute('action') || el.getAttribute('action') === '#';
        return false;
      }).map(el => ({ tag: el.tagName, id: el.id, text: el.textContent.trim().slice(0, 70) })));
      assert.deepEqual(dead, [], `${route}: controles muertos sin JS`);
      assert.ok(await page.locator('main a[href]').count() > 0, `${route}: debe quedar navegación HTML`);
    } finally { await page.close(); }
  }
  await context.close();
  console.log('PASS cuaderno no-JS affordances');
} finally { await browser.close(); }
