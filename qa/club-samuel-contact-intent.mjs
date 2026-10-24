import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });

try {
  for (const mode of ['pointer', 'keyboard']) {
    const context = await browser.newContext();
    await context.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
    const page = await context.newPage();
    await page.goto(`${origin}/clubes-de-lectura/samuel-entre-mundos/`, { waitUntil: 'load' });
    const trigger = page.locator('#invitar a[data-email-reveal][data-email-subject]');
    assert.equal(await trigger.count(), 1);
    if (mode === 'pointer') {
      await trigger.evaluate(el => el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true })));
    } else {
      await trigger.focus();
      await page.keyboard.press('Space');
    }
    const revealed = page.locator('#invitar a[data-email-revealed="true"]');
    assert.equal(await revealed.count(), 1, `${mode}: correo no revelado`);
    const href = await revealed.getAttribute('href');
    assert.ok(href.startsWith('mailto:'), `${mode}: destino no es correo`);
    const parsed = new URL(href);
    assert.equal(parsed.searchParams.get('subject'), 'Club de lectura — Samuel entre mundos');
    assert.match(await revealed.getAttribute('aria-label'), /Enviar correo|@/);
    await context.close();
  }
} finally {
  await browser.close();
}
console.log('club-samuel-contact-intent: OK');