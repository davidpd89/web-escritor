import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const routes = ['/cuaderno/que-es-el-portal-fantasy/', '/recomendaciones/portal-fantasy-espanol/'];
const browser = await chromium.launch();
try {
  for (const route of routes) {
    const context = await browser.newContext({ serviceWorkers: 'block' });
    const page = await context.newPage();
    let requests = 0;
    await context.route('**/*', request => {
      const url = new URL(request.request().url());
      if (url.hostname === 'subscribe.davidpd89.workers.dev') {
        requests++;
        return request.abort();
      }
      return url.origin === ORIGIN ? request.continue() : request.abort();
    });
    await page.goto(ORIGIN + route);
    await page.evaluate(() => { localStorage.removeItem('nl-popup-ts'); localStorage.removeItem('nl-subscribed'); });
    await page.reload();
    await page.evaluate(() => document.dispatchEvent(new MouseEvent('mouseleave', { clientY: -1 })));
    const dialog = page.locator('#nl-popup-dialog[open]');
    await dialog.waitFor();
    await dialog.locator('input[type=email]').fill('lector@');
    await dialog.locator('button[type=submit]').click();
    await assert.doesNotReject(() => dialog.getByRole('status').getByText(/email válido/i).waitFor(), `${route}: falta el error de validación`);
    assert.equal(requests, 0, `${route}: ${requests} solicitudes externas con email inválido`);
    assert.equal(await dialog.locator('input[type=email]').inputValue(), 'lector@', `${route}: se perdió el correo al validar`);
    assert.equal(await dialog.locator('button[type=submit]').isEnabled(), true, `${route}: formulario bloqueado tras error`);
    await context.close();
  }
} finally {
  await browser.close();
}