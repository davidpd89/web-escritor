import assert from 'node:assert/strict';
import { check } from './accesibilidad-fixture.mjs';

await check(async ({ page, origin }) => {
  const nav = page.locator('main nav.editorial-breadcrumb');
  assert.equal(await nav.count(), 1);
  assert.equal(await nav.getAttribute('aria-label'), 'Ruta de navegación');
  const current = nav.locator('[aria-current="page"]');
  assert.equal(await current.count(), 1);
  assert.equal((await current.innerText()).trim(), 'Accesibilidad');
  assert.equal(await current.locator('a').count(), 0);
  const home = nav.locator('a[href="/"]');
  assert.equal(await home.count(), 1);
  await home.focus();
  await page.keyboard.press('Enter');
  await page.waitForURL(`${origin}/`);
  assert.equal(new URL(page.url()).pathname, '/');
  assert.ok(await page.locator('main').count() >= 1);
});
console.log('accesibilidad-breadcrumb-contract: PASS');
