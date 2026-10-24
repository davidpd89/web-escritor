import assert from 'node:assert/strict';
import { withJaula } from './jaula-local-fixture.mjs';

await withJaula(async ({ page, blocked }) => {
  await page.locator('[data-explore-open]').click();
  const dialog = page.locator('#explore-dialog');
  assert.equal(await dialog.evaluate(el => el.open), true);
  const input = dialog.locator('#nl-email-explore');
  for (const email of ['lectora@example.net', 'otra.lectora+jaula@example.org']) {
    await input.fill(email);
    await dialog.locator('.explore-subscribe button[type="submit"]').click();
    await page.waitForFunction(() => document.querySelector('#nl-status-explore')?.textContent.includes('desactivado'));
    assert.equal(await dialog.locator('.explore-subscribe').getAttribute('data-newsletter-source'), 'explore');
    assert.equal(blocked.filter(item => item.method === 'POST' && item.url.includes('subscribe.davidpd89.workers.dev')).length, 0, 'El formulario intentó registrar un contacto real');
  }
  assert.equal(await input.isEnabled(), true, 'La desactivación debe informar sin destruir el formulario');
});
console.log('jaula-staging-newsletter-browser: OK');
