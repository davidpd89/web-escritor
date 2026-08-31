import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const SUBSCRIBE_URL = 'https://subscribe.davidpd89.workers.dev/';

const browser = await chromium.launch({ headless: true });
try {
  const context = await browser.newContext({
    viewport: { width: 1280, height: 900 },
    reducedMotion: 'reduce'
  });
  const page = await context.newPage();

  let requestCount = 0;
  let lastPayload = null;
  await page.route('https://subscribe.davidpd89.workers.dev/**', async (route) => {
    requestCount += 1;
    lastPayload = route.request().postDataJSON();
    await route.fulfill({
      // The production Worker returns 201 Created for a DOI contact pending
      // confirmation. Mirror that contract here instead of a permissive 200.
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({ ok: true, state: 'pending_confirmation' })
    });
  });

  await page.addInitScript(() => {
    try {
      localStorage.removeItem('nl-popup-ts');
      localStorage.removeItem('nl-subscribed');
    } catch {}
  });

  const response = await page.goto(`${ORIGIN}/cuaderno/que-es-el-portal-fantasy/`, { waitUntil: 'networkidle' });
  assert.ok(response?.ok(), 'representative Cuaderno article must load');

  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
  const dialog = page.locator('#nl-popup-dialog');
  await dialog.waitFor({ state: 'visible' });
  assert.equal(await dialog.getAttribute('open'), '', 'newsletter popup must open after the scroll trigger');

  const email = dialog.locator('#nl-popup-email');
  const consent = dialog.locator('#nl-popup-gdpr');
  const status = dialog.locator('#nl-popup-status');
  const submit = dialog.locator('#nl-popup-submit');

  await email.fill('qa-newsletter@example.com');
  assert.equal(await consent.isChecked(), false, 'privacy consent must start unchecked');
  assert.equal(await consent.getAttribute('required'), '', 'privacy consent must be required');

  await submit.click();
  // The handler runs through scheduleTask()/scheduler.postTask. The status
  // element is already visible before submit, so waiting for visibility races
  // the async handler and can read the initial empty string. Wait for the
  // observable message instead.
  await page.waitForFunction(() => /Acepta la política de privacidad/i.test(
    document.querySelector('#nl-popup-status')?.textContent || ''
  ));
  assert.match(await status.textContent(), /Acepta la política de privacidad/i,
    'unchecked submit must explain that privacy consent is required');
  assert.equal(requestCount, 0, 'unchecked popup must not contact the subscription Worker');

  await consent.check();
  await submit.click();
  await page.waitForFunction(() => document.querySelector('#nl-popup-panel')?.textContent?.includes('Revisa tu correo'));

  assert.equal(requestCount, 1, 'checked popup must issue exactly one subscription request');
  assert.deepEqual(lastPayload, {
    email: 'qa-newsletter@example.com',
    source: 'popup',
    website: ''
  }, 'popup must preserve the existing Worker payload contract');
  assert.ok(!Object.hasOwn(lastPayload, 'consent'), 'popup must not invent a consent field in the Worker payload');

  await context.close();
  console.log('newsletter-consent-browser: popup unchecked/checked contract passed');
} finally {
  await browser.close();
}
