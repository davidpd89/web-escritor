import assert from 'node:assert/strict';
import { check } from './accesibilidad-fixture.mjs';

await check(async ({ page, origin }) => {
  assert.ok(await page.locator('noscript nav.primary-nav a[href="/libros/"]').count() === 1);
  assert.ok((await page.locator('main').innerText()).length > 500);
  const skip = page.locator('a.skip-link');
  await skip.focus();
  await page.keyboard.press('Enter');
  await page.waitForURL(`${origin}/accesibilidad/#contenido`);
  assert.equal(await page.locator('#contenido').count(), 1);
  const contact = page.locator('main a[data-email-reveal]');
  assert.equal(await contact.getAttribute('href'), '/prensa.html#contacto');
  await contact.click();
  await page.waitForURL(`${origin}/prensa.html#contacto`);
  assert.equal(await page.locator('section#contacto').count(), 1);
  assert.ok((await page.locator('section#contacto').innerText()).length > 100);
}, { javaScriptEnabled: false });
console.log('accesibilidad-nojs-contact: PASS');
