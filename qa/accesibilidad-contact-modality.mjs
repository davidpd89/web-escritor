import assert from 'node:assert/strict';
import { check } from './accesibilidad-fixture.mjs';

await check(async ({ page }) => {
  for (const mode of ['pointer', 'Enter', 'Space']) {
    await page.goto('http://127.0.0.1:' + new URL(page.url()).port + '/accesibilidad/', { waitUntil: 'load' });
    const initial = page.locator('main a[data-email-reveal]');
    assert.equal(await initial.count(), 1);
    assert.ok((await initial.getAttribute('href')).includes('/prensa.html#contacto'));
    await initial.focus();
    if (mode === 'pointer') await initial.click({ noWaitAfter: true });
    else await page.keyboard.press(mode);
    await page.waitForFunction(() => Boolean(document.querySelector('main a[data-email-revealed="true"]')));
    const revealed = page.locator('main a[data-email-revealed="true"]');
    assert.ok((await revealed.getAttribute('href')).startsWith('mailto:'), mode);
    assert.ok((await revealed.getAttribute('aria-label')).includes('@'), mode);
    assert.equal(await page.evaluate(() => document.activeElement?.getAttribute('data-email-revealed')), 'true', mode);
  }
});
console.log('accesibilidad-contact-modality: PASS');
