import assert from 'node:assert/strict';
import { startSite, launch } from '../qa/errores-progresivo-browser-fixture.mjs';
const site = await startSite();
const browser = await launch();
try {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  const response = await page.goto(site.origin + '/__missing_recovery_probe__/', { waitUntil: 'domcontentloaded' });
  assert.equal(response.status(), 404, 'Missing route must send an actual HTTP 404');
  assert.equal(await page.locator('h1').count(), 1);
  assert.equal(await page.locator('main#contenido').count(), 1);
  assert.match(await page.locator('meta[name=robots]').getAttribute('content'), /noindex/i);
  assert.equal(await page.locator('link[rel=canonical]').count(), 0,
    '404 should not canonicalize an absent page to an indexable route');
  assert.equal(await page.locator('a.skip-link[href="#contenido"]').count(), 1);
  await context.close();
} finally { await browser.close(); await site.close(); }
console.log('PASS 404 HTTP, SEO and skip target');
