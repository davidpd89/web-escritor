import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const sentinel = 'MANUSCRITO_PRIVADO_QA_582931';
const cases = [
  { route: '/herramientas/dialogo/', input: '#dialogue-text', submit: '[data-dialogue-tool] button[type="submit"]', result: '[data-dialogue-results]' },
  { route: '/herramientas/repeticiones/', input: '[data-repetition-input]', submit: '[data-repetition-form] button[type="submit"]', result: '[data-repetition-results]' }
];
const browser = await chromium.launch();
try {
  for (const item of cases) {
    const context = await browser.newContext();
    const page = await context.newPage();
    const leaks = [];
    await context.route('**/*', async route => {
      const request = route.request();
      const url = new URL(request.url());
      const local = url.origin === new URL(origin).origin;
      if (!local) {
        const payload = `${request.url()} ${request.postData() || ''}`;
        if (payload.includes(sentinel)) leaks.push(payload);
        await route.abort();
      } else {
        await route.continue();
      }
    });
    try {
      const response = await page.goto(new URL(item.route, origin).href);
      assert.equal(response.status(), 200, `${item.route}: HTTP`);
      await page.locator(item.input).fill(`${sentinel}. Ana abrió la puerta. La puerta estaba abierta. —No entres —dijo Ana—. No todavía.`);
      await page.locator(item.submit).focus();
      await page.keyboard.press('Enter');
      await page.locator(item.result).waitFor({ state: 'visible', timeout: 10000 });
      assert.deepEqual(leaks, [], `${item.route}: el manuscrito aparece en solicitudes externas`);
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}
