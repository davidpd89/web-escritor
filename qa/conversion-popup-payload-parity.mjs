import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const routes = ['/cuaderno/que-es-el-portal-fantasy/', '/recomendaciones/portal-fantasy-espanol/'];
const browser = await chromium.launch();
try {
  for (const route of routes) {
    const context = await browser.newContext({ serviceWorkers: 'block' });
    const payloads = [];
    await context.route('**/*', request => {
      const url = new URL(request.request().url());
      if (url.hostname === 'subscribe.davidpd89.workers.dev') {
        if (request.request().method() === 'POST') {
          payloads.push(JSON.parse(request.request().postData()));
        }
        return request.fulfill({ status: 200, contentType: 'application/json', headers: { 'access-control-allow-origin': ORIGIN }, body: JSON.stringify({ ok: true, state: 'pending_confirmation' }) });
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
    await dialog.getByText('Solicitud recibida').waitFor();
    assert.equal(payloads.length, 1, `${route}: ${payloads.length} solicitudes para una activación`);
    assert.deepEqual(Object.keys(payloads[0]).sort(), ['email', 'source', 'website'], `${route}: campos transmitidos distintos del contrato público`);
    assert.equal(payloads[0].email, 'lector@example.com', `${route}: correo transmitido incorrecto`);
    assert.equal(payloads[0].source, 'popup', `${route}: origen de conversión incorrecto`);
    assert.equal(payloads[0].website, '', `${route}: honeypot inesperadamente poblado`);
    await context.close();
  }
} finally {
  await browser.close();
}