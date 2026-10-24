import assert from 'node:assert/strict';
import { startSite, launch } from '../qa/errores-progresivo-browser-fixture.mjs';
const site = await startSite();
const browser = await launch();
try {
  const page = await browser.newPage({ viewport: { width: 390, height: 700 } });
  await page.route('**/assets/v1-shell.js*', route => route.abort());
  await page.route('**/assets/newsletter-general.js*', route => route.abort());
  await page.goto(site.origin + '/__broken_script_recovery__', { waitUntil: 'domcontentloaded' });
  const links = page.locator('main .findability-recovery a[href]');
  assert((await links.count()) >= 6, 'Missing recovery choices when JS fails');
  assert(await page.getByRole('link', { name: 'Volver al inicio' }).isVisible());
  const hrefs = await links.evaluateAll(nodes => nodes.map(n => n.getAttribute('href')));
  assert(hrefs.every(h => h.startsWith('/') && !h.startsWith('//')));
  for (const href of hrefs) {
    const result = await page.request.get(site.origin + href);
    assert.equal(result.status(), 200, `Recovery destination broken: ${href}`);
  }
  await page.getByRole('link', { name: 'Volver al inicio' }).click();
  assert.equal(new URL(page.url()).pathname, '/');
  assert(await page.locator('main').first().isVisible(), 'Recovery link led to an empty page');
  await page.close();
} finally { await browser.close(); await site.close(); }
console.log('PASS 404 recovery when shell JS is blocked');
