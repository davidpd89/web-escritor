import assert from 'node:assert/strict';
import { withSite } from './gracias-matrix-harness.mjs';

await withSite(async ({ open }) => {
  const { page, context } = await open('/gracias-suscripcion/', {}, async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem('nl-subscribed', '1'));
  });
  assert.equal(await page.evaluate(() => localStorage.getItem('nl-subscribed')), '1',
    'Test precondition: returning confirmed browser');
  await page.locator('[data-explore-open]').first().click();
  const form = page.locator('#newsletter-form-explore');
  const actionable = await form.isVisible() && await form.locator('button[type=submit]').isEnabled();
  assert.equal(actionable, false,
    'A confirmed return page must not offer another active subscription form in Explore');
  await context.close();
});
console.log('PASS confirmed user Explore CTA consistency');
