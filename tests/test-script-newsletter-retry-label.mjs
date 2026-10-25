import assert from 'node:assert/strict';
import { startSite, launch } from '../qa/errores-progresivo-browser-fixture.mjs';
const html = '<!doctype html><html><body><span data-samuel-quiz hidden></span><form novalidate id="newsletter-form-home"><label for="nl-email-home">Email</label><input id="nl-email-home" type="email" aria-describedby="nl-status-home"><button type="submit">Recibir novedades</button><p id="nl-status-home" role="status" aria-live="polite"></p></form><script src="/script.js"></script></body></html>';
const site = await startSite({ '/__qa/newsletter.html': html });
const browser = await launch();
try {
  const context = await browser.newContext();
  await context.addInitScript(() => {
    window.DPNewsletterGeneral = { postNewsletter: async () => ({ ok: false, code: 'network_error' }) };
  });
  const page = await context.newPage();
  await page.goto(site.origin + '/__qa/newsletter.html');
  await page.locator('#nl-email-home').fill('valid@example.org');
  await page.locator('#newsletter-form-home button').click();
  await page.waitForFunction(() => document.querySelector('#nl-status-home').textContent.includes('Error'));
  assert.equal(await page.locator('#newsletter-form-home button').innerText(), 'Recibir novedades',
    'Failed request must restore the original per-form submit label');
  assert.equal(await page.locator('#newsletter-form-home button').isEnabled(), true);
  await context.close();
} finally { await browser.close(); await site.close(); }
console.log('PASS newsletter failed-request label restoration');
