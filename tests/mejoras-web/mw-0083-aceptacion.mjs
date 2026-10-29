import assert from 'node:assert/strict';
import { chromium } from 'playwright';

// MW-0083: Escape cierra el submenú de la cabecera y devolver el foco al botón no lo reabre.
const origin = process.env.SITE_ORIGIN;
assert.ok(origin, 'SITE_ORIGIN debe apuntar al servidor local del repositorio');

const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' });
  await page.addInitScript(() => { try { sessionStorage.setItem('dp-intro-seen', '1'); } catch (e) {} });
  await page.goto(`${origin.replace(/\/$/, '')}/`, { waitUntil: 'load', timeout: 20000 });
  const trigger = page.locator('.masthead-nav__item > .masthead-nav__submenu-trigger').first();
  await trigger.waitFor({ state: 'attached', timeout: 10000 });
  await trigger.scrollIntoViewIfNeeded();
  await trigger.focus();
  const firstLink = page.locator('.masthead-nav__item:first-child .masthead-nav__submenu a').first();
  await firstLink.focus();
  const visible = () => page.evaluate(() => {
    const li = document.querySelector('.masthead-nav__item');
    const sub = li.querySelector(':scope > .masthead-nav__submenu');
    const cs = getComputedStyle(sub);
    return { visibility: cs.visibility, dismissed: li.classList.contains('is-dismissed') };
  });
  await page.waitForTimeout(300);
  assert.equal((await visible()).visibility, 'visible', 'con el foco dentro el submenú se abre');
  await page.keyboard.press('Escape');
  await page.waitForTimeout(400);
  const after = await visible();
  assert.equal(after.dismissed, true, 'Escape deja el submenú descartado');
  assert.equal(after.visibility, 'hidden', 'Escape no debe reabrir el submenú al devolver el foco al botón');
  assert.equal(await page.evaluate(() => document.activeElement === document.querySelector('.masthead-nav__item > .masthead-nav__submenu-trigger')), true, 'el foco vuelve al botón');
  console.log('PASS MW-0083: Escape cierra el submenú y el foco vuelve al botón');
} finally {
  await browser.close();
}
