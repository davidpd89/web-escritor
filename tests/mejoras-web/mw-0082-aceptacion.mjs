import assert from 'node:assert/strict';
import { chromium } from 'playwright';

// MW-0082: «Volver arriba» devuelve el recorrido del teclado al principio de la página.
const origin = process.env.SITE_ORIGIN;
assert.ok(origin, 'SITE_ORIGIN debe apuntar al servidor local del repositorio');

const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 }, reducedMotion: 'reduce' });
  await page.addInitScript(() => { try { sessionStorage.setItem('dp-intro-seen', '1'); } catch (e) {} });
  await page.goto(`${origin.replace(/\/$/, '')}/`, { waitUntil: 'load', timeout: 20000 });
  const button = page.locator('button.back-to-top');
  await button.waitFor({ state: 'attached', timeout: 10000 });
  await page.evaluate(() => window.scrollTo(0, 2000));
  await page.waitForFunction(() => document.querySelector('button.back-to-top')?.classList.contains('is-visible'));
  await button.focus();
  assert.equal(await page.evaluate(() => document.activeElement?.classList.contains('back-to-top')), true, 'el botón recibe el foco');
  await page.keyboard.press('Enter');
  await page.waitForFunction(() => window.scrollY < 5);
  await page.keyboard.press('Tab');
  const where = await page.evaluate(() => ({ cls: document.activeElement?.className || '', tag: document.activeElement?.tagName }));
  assert.match(where.cls, /skip-link/, `tras «Volver arriba», la siguiente tabulación llega al principio (skip-link); llegó a ${where.tag}.${where.cls}`);
  assert.equal(await page.evaluate(() => document.body.hasAttribute('tabindex')), false, 'no se deja tabindex residual en body');
  console.log('PASS MW-0082: Volver arriba reinicia el orden de tabulación y no deja tabindex residual');
} finally {
  await browser.close();
}
