import assert from 'node:assert/strict';
import { startSite, launch } from '../qa/errores-progresivo-browser-fixture.mjs';
const site = await startSite();
const browser = await launch();
try {
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto(site.origin + '/libros/');
  await page.goto(site.origin + '/offline.html');
  const back = page.locator('[data-back]');
  assert(await back.isVisible(), 'Back must be operable with a real previous site page');
  await back.click();
  await page.waitForURL('**/libros/');
  assert.equal(new URL(page.url()).pathname, '/libros/');
  const direct = await context.newPage();
  await direct.goto(site.origin + '/offline.html');
  assert.equal(await direct.locator('[data-back]').isVisible(), false,
    'Direct entry without a useful previous page must not offer a false Back action');
  await context.close();
} finally { await browser.close(); await site.close(); }
console.log('PASS offline browser-history recovery');
