import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });

const cases = [
  ['/fragmento/', '#newsletter-form-fragmento'],
  ['/las-manecillas-del-recuerdo/', '#newsletter-form-manecillas'],
  ['/cuaderno/', '#newsletter-form-cuaderno']
];

try {
  const context = await browser.newContext();
  for (const [path, selector] of cases) {
    const page = await context.newPage();
    await page.addInitScript(() => {
      try { localStorage.setItem('nl-popup-ts', String(Date.now())); } catch {}
    });
    const response = await page.goto(ORIGIN + path, { waitUntil: 'domcontentloaded' });
    assert.ok(response?.ok(), `${path}: HTTP válido`);
    const form = page.locator(selector);
    await form.waitFor({ state: 'visible' });
    const email = form.locator('input[type="email"]');
    await email.fill('correo-invalido');
    await form.locator('[type="submit"]').click();
    const status = form.locator('[role="status"]');
    await status.getByText(/Introduce un email válido/i).waitFor();
    const result = await email.evaluate(el => {
      const form = el.form;
      const status = form.querySelector('[role="status"]');
      const ids = (el.getAttribute('aria-describedby') || '').split(/\s+/);
      const errorId = el.getAttribute('aria-errormessage');
      const associated = [...ids, errorId].some(id => id && document.getElementById(id) === status);
      return {
        associated,
        invalid: el.getAttribute('aria-invalid') === 'true' || (!el.validity.valid && !form.noValidate),
        focused: document.activeElement === el,
        message: status?.textContent?.trim()
      };
    });
    assert.ok(result.associated, `${path}: el error ${JSON.stringify(result.message)} no está asociado al campo de email`);
    assert.ok(result.invalid, `${path}: el email rechazado no comunica estado inválido`);
    assert.ok(result.focused, `${path}: el foco debe regresar al email rechazado`);
    await page.close();
  }
  await context.close();
} finally {
  await browser.close();
}
console.log('newsletter-invalid-email-a11y-browser: PASS');
