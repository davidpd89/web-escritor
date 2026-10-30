import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const browser = await chromium.launch({
  headless: true,
  ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {})
});

try {
  const context = await browser.newContext({ reducedMotion: 'reduce', serviceWorkers: 'block' });
  // No real subscription, analytics, or other third-party request is sent.
  await context.route('**/*', route => {
    const url = new URL(route.request().url());
    if (url.origin === ORIGIN) return route.continue();
    if (url.hostname === 'subscribe.davidpd89.workers.dev') return route.fulfill({
      status: 201, contentType: 'application/json',
      body: JSON.stringify({ ok: true, state: 'pending_confirmation' })
    });
    return route.abort();
  });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(`${ORIGIN}/cuaderno/que-es-el-portal-fantasy/`, { waitUntil: 'load' });
  await page.locator('h1').evaluate(el => { el.tabIndex = -1; el.focus({ preventScroll: true }); });
  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
  const dialog = page.locator('#nl-popup-dialog');
  await dialog.waitFor({ state: 'visible' });
  await dialog.locator('#nl-popup-email').fill('qa-popup@example.invalid');
  await dialog.locator('#nl-popup-submit').click();
  await dialog.getByText('Solicitud recibida', { exact: true }).waitFor();

  assert.deepEqual(await dialog.evaluate(el => {
    const text = attr => document.getElementById(el.getAttribute(attr))?.textContent?.trim() || null;
    return { title: text('aria-labelledby'), description: text('aria-describedby') };
  }), {
    title: 'Solicitud recibida',
    description: 'Revisa tu correo para confirmar si aún no lo habías hecho.'
  }, 'Success must preserve the dialog accessible name and description');
  assert.equal(await dialog.locator('#nl-popup-close').count(), 1, 'Success still needs a close control');
  await page.keyboard.press('Tab');
  assert.equal(await page.evaluate(() => document.activeElement?.id), 'nl-popup-skip');
  await page.keyboard.press('Tab');
  assert.equal(await page.evaluate(() => document.activeElement?.id), 'nl-popup-close');
  await page.keyboard.press('Shift+Tab');
  assert.equal(await page.evaluate(() => document.activeElement?.id), 'nl-popup-skip');
  await dialog.locator('#nl-popup-skip').click();
  await dialog.waitFor({ state: 'detached' });
  assert.equal(await page.evaluate(() => document.activeElement?.tagName), 'H1', 'Closing must restore focus');
  assert.ok(await page.evaluate(() => localStorage.getItem('nl-requested')));
  await page.reload({ waitUntil: 'load' });
  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
  assert.equal(await page.locator('#nl-popup-dialog').count(), 0, 'Requested subscription must suppress the popup');
  assert.deepEqual(errors, [], 'No uncaught browser errors');
  await context.close();
} finally {
  await browser.close();
}
console.log('newsletter-popup-success-browser: PASS');