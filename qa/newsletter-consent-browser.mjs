import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const WORKER_PATTERN = 'https://subscribe.davidpd89.workers.dev/**';

async function pageWithWorker(context) {
  const page = await context.newPage();
  const requests = [];
  await page.route(WORKER_PATTERN, async (route) => {
    requests.push(route.request().postDataJSON());
    await route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({ ok: true, state: 'pending_confirmation' })
    });
  });
  return { page, requests };
}

async function assertGeneralFlow(context, spec) {
  const { page, requests } = await pageWithWorker(context);
  await page.addInitScript(() => {
    try { localStorage.setItem('nl-popup-ts', String(Date.now())); } catch {}
  });
  const response = await page.goto(`${ORIGIN}${spec.path}`, { waitUntil: 'domcontentloaded' });
  assert.ok(response?.ok(), `${spec.name}: page must load`);

  if (spec.openExplore) {
    const trigger = page.locator('[data-explore-open]').first();
    await trigger.click();
    await page.locator('[data-explore-dialog]').waitFor({ state: 'visible' });
  }
  if (spec.shellOnly) {
    assert.equal(await page.locator('script[src*="/script.js"]').count(), 0,
      `${spec.name}: shell-only fixture must remain independent from script.js`);
  }

  const form = page.locator(spec.form);
  const email = page.locator(spec.email);
  const consent = page.locator(spec.consent);
  const status = page.locator(spec.status);
  await form.waitFor({ state: 'attached' });
  await email.fill(`qa-${spec.source}@example.com`);
  assert.equal(await consent.isChecked(), false, `${spec.name}: consent starts unchecked`);
  assert.equal(await consent.getAttribute('required'), '', `${spec.name}: consent is required`);

  await form.locator('[type="submit"]').click();
  await page.waitForFunction((selector) => /Acepta la política de privacidad/i.test(
    document.querySelector(selector)?.textContent || ''
  ), spec.status);
  assert.match(await status.textContent(), /Acepta la política de privacidad/i,
    `${spec.name}: unchecked submit explains consent`);
  assert.equal(requests.length, 0, `${spec.name}: unchecked submit must make zero requests`);

  await consent.check();
  await form.locator('[type="submit"]').click();
  await page.waitForFunction((selector) => /Revisa tu correo/i.test(
    document.querySelector(selector)?.textContent || ''
  ), spec.form);
  assert.equal(requests.length, 1, `${spec.name}: checked submit must make exactly one request`);
  assert.deepEqual(requests[0], {
    email: `qa-${spec.source}@example.com`,
    source: spec.source,
    website: ''
  }, `${spec.name}: Worker payload must stay exact`);
  assert.ok(!Object.hasOwn(requests[0], 'consent'), `${spec.name}: payload must not contain consent`);
  await page.close();
}

const browser = await chromium.launch({ headless: true });
try {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, reducedMotion: 'reduce' });

  for (const spec of [
    { name: 'Fragmento inline', path: '/fragmento/', form: '#newsletter-form-fragmento', email: '#nl-email-fragmento', consent: '#nl-gdpr-fragmento', status: '#nl-status-fragmento', source: 'fragmento' },
    { name: 'Manecillas inline', path: '/las-manecillas-del-recuerdo/', form: '#newsletter-form-manecillas', email: '#nl-email-manecillas', consent: '#nl-gdpr-manecillas', status: '#nl-status-manecillas', source: 'manecillas' },
    { name: 'Cuaderno inline', path: '/cuaderno/', form: '#newsletter-form-cuaderno', email: '#nl-email-cuaderno', consent: '#nl-gdpr-cuaderno', status: '#nl-status-cuaderno', source: 'cuaderno' },
    { name: 'Explore with script.js', path: '/fragmento/', form: '#newsletter-form-explore', email: '#nl-email-explore', consent: '#nl-gdpr-explore', status: '#nl-status-explore', source: 'explore', openExplore: true },
    { name: 'Explore shell-only', path: '/privacidad.html', form: '#newsletter-form-explore', email: '#nl-email-explore', consent: '#nl-gdpr-explore', status: '#nl-status-explore', source: 'explore', openExplore: true, shellOnly: true }
  ]) {
    await assertGeneralFlow(context, spec);
  }

  const { page, requests } = await pageWithWorker(context);
  await page.addInitScript(() => {
    try {
      localStorage.removeItem('nl-popup-ts');
      localStorage.removeItem('nl-subscribed');
    } catch {}
  });
  const response = await page.goto(`${ORIGIN}/cuaderno/que-es-el-portal-fantasy/`, { waitUntil: 'domcontentloaded' });
  assert.ok(response?.ok(), 'popup representative article must load');
  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
  const dialog = page.locator('#nl-popup-dialog');
  await dialog.waitFor({ state: 'visible' });
  const email = dialog.locator('#nl-popup-email');
  const consent = dialog.locator('#nl-popup-gdpr');
  const status = dialog.locator('#nl-popup-status');
  const submit = dialog.locator('#nl-popup-submit');
  await email.fill('qa-newsletter@example.com');
  assert.equal(await consent.isChecked(), false, 'popup consent starts unchecked');
  await submit.click();
  await page.waitForFunction(() => /Acepta la política de privacidad/i.test(document.querySelector('#nl-popup-status')?.textContent || ''));
  assert.match(await status.textContent(), /Acepta la política de privacidad/i, 'popup unchecked submit explains consent');
  assert.equal(requests.length, 0, 'popup unchecked submit makes zero requests');
  await consent.check();
  await submit.click();
  await page.waitForFunction(() => document.querySelector('#nl-popup-panel')?.textContent?.includes('Revisa tu correo'));
  assert.equal(requests.length, 1, 'popup checked submit makes exactly one request');
  assert.deepEqual(requests[0], { email: 'qa-newsletter@example.com', source: 'popup', website: '' }, 'popup payload stays exact');
  await page.close();

  const strict = await context.newPage();
  const strictResponse = await strict.goto(`${ORIGIN}/herramientas/manuscrito/`, { waitUntil: 'domcontentloaded' });
  assert.ok(strictResponse?.ok(), 'local-only manuscript tool must load');
  await strict.locator('[data-explore-open]').first().click();
  await strict.locator('[data-explore-dialog]').waitFor({ state: 'visible' });
  assert.equal(await strict.locator('#newsletter-form-explore').count(), 0,
    'local-only CSP page must not expose an unusable newsletter form');
  assert.equal(await strict.locator('script[src*="newsletter-general.js"]').count(), 0,
    'local-only CSP page must not load the newsletter runtime');
  await strict.close();

  await context.close();
  console.log('newsletter-consent-browser: inline + Explore + shell-only + popup + local-only CSP contracts passed');
} finally {
  await browser.close();
}
