import test from 'node:test';
import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = process.env.BASE_URL || process.env.TEST_BASE_URL || 'http://127.0.0.1:8000';

test('accesibilidad: la confirmación pendiente conserva un anuncio accesible', async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    await page.route('**/subscribe.davidpd89.workers.dev/**', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, state: 'pending_confirmation' }) }));
    await page.goto(new URL('/accesibilidad/', base).href);
    const form = page.locator('#newsletter-form-explore');
    await page.locator('[data-explore-open]').click();
    await form.locator('input[type=email]').fill('lectora@example.com');
    await form.locator('button[type=submit]').click();
    await page.getByText(/solicitud recibida/i).waitFor();
    const result = await form.evaluate(element => {
      const message = [...element.querySelectorAll('*')].find(node => node.children.length === 0 && /solicitud recibida/i.test(node.textContent || ''));
      if (!message) return { announced: false, text: '' };
      let node = message;
      let announced = false;
      while (node && node !== element.parentElement) {
        if (['status', 'alert'].includes(node.getAttribute?.('role')) || ['polite', 'assertive'].includes(node.getAttribute?.('aria-live'))) announced = true;
        node = node.parentElement;
      }
      return { announced, text: message.textContent };
    });
    assert.equal(result.announced, true, '/accesibilidad/: confirmación pendiente sin región de anuncio accesible');
    assert.match(result.text, /confirmar|confirmación/i, '/accesibilidad/: la respuesta pendiente debe explicar la confirmación por correo');
  } finally {
    await browser.close();
  }
});