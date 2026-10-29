import assert from 'node:assert/strict';
import { chromium } from 'playwright';

// MW-0012: mientras la introducción de la portada está activa, «Saltar al contenido» es visible y funcional.
const origin = process.env.SITE_ORIGIN;
assert.ok(origin, 'SITE_ORIGIN debe apuntar al servidor local del repositorio');

const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  await page.addInitScript(() => { try { localStorage.setItem('nl-subscribed', '1'); } catch (e) {} });
  await page.goto(`${origin.replace(/\/$/, '')}/`, { waitUntil: 'load', timeout: 20000 });
  await page.waitForFunction(() => document.documentElement.classList.contains('intro-lock'), null, { timeout: 10000 });

  await page.keyboard.press('Tab');
  await page.waitForTimeout(500);
  const skip = await page.evaluate(() => {
    const a = document.activeElement;
    const r = a.getBoundingClientRect();
    const top = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
    return { cls: a.className, visible: !!top && (top === a || a.contains(top)) };
  });
  assert.match(skip.cls, /skip-link/, 'la primera tabulación llega a «Saltar al contenido»');
  assert.equal(skip.visible, true, 'con el foco, el enlace se ve por encima de la introducción');

  await page.keyboard.press('Enter');
  await page.waitForFunction(() => document.querySelector('[data-intro]')?.hidden === true, null, { timeout: 5000 });
  assert.equal(await page.evaluate(() => document.documentElement.classList.contains('intro-lock')), false, 'la introducción se cierra');
  assert.equal(await page.evaluate(() => document.activeElement?.id), 'contenido', 'el foco queda en el contenido principal');
  console.log('PASS MW-0012: «Saltar al contenido» visible sobre la introducción y cierra la introducción llevando el foco al contenido');
} finally {
  await browser.close();
}
