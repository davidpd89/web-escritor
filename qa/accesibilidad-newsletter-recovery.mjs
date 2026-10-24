import assert from 'node:assert/strict';
import { check } from './accesibilidad-fixture.mjs';

await check(async ({ page }) => {
  let outgoing = 0;
  page.on('request', request => { if (request.url().includes('subscribe.davidpd89.workers.dev')) outgoing++; });
  await page.locator('[data-explore-open]').first().click();
  const form = page.locator('#newsletter-form-explore');
  const email = form.locator('input[type="email"]');
  const status = form.locator('[role="status"]');
  const submit = form.locator('[type="submit"]');
  assert.equal(await status.getAttribute('aria-live'), 'polite');
  for (const invalid of ['', 'sin-arroba', 'a@b', 'x'.repeat(65) + '@example.org']) {
    await email.fill(invalid);
    await submit.click();
    await page.waitForFunction(() => document.querySelector('#nl-status-explore')?.textContent.includes('email válido'));
    assert.equal(await page.evaluate(() => document.activeElement?.id), 'nl-email-explore');
    assert.equal(outgoing, 0, `Petición para ${invalid}`);
  }
  await email.fill('lectora@example.org');
  await submit.click();
  await page.waitForFunction(() => document.querySelector('#nl-status-explore')?.textContent.includes('Error al suscribirse'));
  assert.equal(await submit.isEnabled(), true);
  assert.equal(await submit.innerText(), 'Recibir novedades');
  assert.equal(outgoing, 1);
});
console.log('accesibilidad-newsletter-recovery: PASS');
