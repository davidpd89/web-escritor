import assert from 'node:assert/strict';
import {withPage} from './microstory-offline-harness.mjs';

await withPage(async ({page}) => {
  let requests=0;
  page.on('request',r => {if (r.url().includes('subscribe.davidpd89.workers.dev')) requests++;});
  await page.locator('[data-explore-open]').click();
  const form = page.locator('#newsletter-form-explore');
  assert.equal(await form.getAttribute('data-newsletter-bound'),'true');
  const input=form.locator('input[type=email]');
  const submit=form.locator('[type=submit]');
  for (const value of ['', 'sin-arroba', 'a@b', 'a@b.c', 'x'.repeat(255)+'@example.com', '<script>alert(1)</script>']) {
    await input.fill(value);
    await submit.click();
    await page.waitForFunction(() => document.querySelector('#nl-status-explore')?.textContent.includes('email válido'));
    assert.equal(await input.inputValue(),value);
    assert.equal(await input.evaluate(e=>document.activeElement===e),true);
    assert.equal(requests,0,`Unexpected request for ${value}`);
    assert.equal(await form.locator('[role=status]').getAttribute('aria-live'),'polite');
  }
});
console.log('PASS microstory newsletter invalid input');
