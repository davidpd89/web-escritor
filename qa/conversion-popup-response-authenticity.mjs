import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const browser = await chromium.launch();
const route = '/cuaderno/que-es-el-portal-fantasy/';
try {
  const context = await browser.newContext({ serviceWorkers: 'block' });
  await context.route('**/*', request => {
    const url = new URL(request.request().url());
    if (url.hostname === 'subscribe.davidpd89.workers.dev') {
      return request.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, state: 'unexpected' }), headers: { 'access-control-allow-origin': ORIGIN } });
    }
    return url.origin === ORIGIN ? request.continue() : request.abort();
  });
  const page = await context.newPage();
  await page.goto(ORIGIN + route);
  await page.evaluate(() => { localStorage.removeItem('nl-popup-ts'); localStorage.removeItem('nl-subscribed'); });
  await page.reload();
  await page.evaluate(() => document.dispatchEvent(new MouseEvent('mouseleave', { clientY: -1 })));
  const dialog = page.locator('#nl-popup-dialog[open]');
  await dialog.waitFor();
  await dialog.locator('input[type=email]').fill('lector@example.com');
  await dialog.locator('button[type=submit]').click();
  await dialog.getByRole('status').getByText(/error|inténtalo/i).waitFor();
  assert.equal(await dialog.locator('input[type=email]').count(), 1, `${route}: desapareció el formulario tras una respuesta no confirmada`);
  assert.equal(await dialog.locator('button[type=submit]').isEnabled(), true, `${route}: no puede reintentarse la solicitud`);
  assert.equal(await dialog.getByText('Solicitud recibida').count(), 0, `${route}: falso mensaje de éxito`);
  await context.close();
} finally {
  await browser.close();
}