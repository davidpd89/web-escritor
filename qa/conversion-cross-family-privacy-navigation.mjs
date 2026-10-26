import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const routes = ['/cuaderno/que-es-el-portal-fantasy/', '/recomendaciones/portal-fantasy-espanol/', '/universo/noveris/', '/clubes-de-lectura/samuel-entre-mundos/'];
const browser = await chromium.launch({ headless: true });
try {
  for (const route of routes) {
    const context = await browser.newContext({ serviceWorkers: 'block', viewport: { width: 1280, height: 800 } });
    const page = await context.newPage();
    const submissions = [];
    await context.route('**/*', request => {
      const url = new URL(request.request().url());
      if (url.hostname === 'subscribe.davidpd89.workers.dev') {
        submissions.push(url.href);
        return request.abort();
      }
      return url.origin === ORIGIN ? request.continue() : request.abort();
    });
    const response = await page.goto(ORIGIN + route);
    assert.equal(response.status(), 200, `${route}: documento inaccesible`);
    await page.evaluate(() => localStorage.removeItem('nl-popup-ts'));
    await page.evaluate(() => localStorage.removeItem('nl-subscribed'));
    await page.reload();
    await page.evaluate(() => document.dispatchEvent(new MouseEvent('mouseleave', { bubbles: true, clientY: -1 })));
    const dialog = page.locator('#nl-popup-dialog[open]');
    await dialog.waitFor();
    const privacy = dialog.getByRole('link', { name: /política de privacidad/i });
    assert.equal(await privacy.count(), 1, `${route}: enlace de privacidad ausente o duplicado`);
    assert.equal(new URL(await privacy.getAttribute('href'), ORIGIN).pathname, '/privacidad.html', `${route}: destino de privacidad incorrecto`);
    await privacy.click();
    await page.waitForURL('**/privacidad.html');
    assert.match(await page.locator('h1').innerText(), /privacidad/i, `${route}: documento de privacidad sin encabezado`);
    assert.deepEqual(submissions, [], `${route}: se transmitió una suscripción sin consentimiento`);
    await context.close();
  }
} finally {
  await browser.close();
}