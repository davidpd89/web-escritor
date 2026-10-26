import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const PATH = '/fragmento/';
const browser = await chromium.launch({ headless: true });

try {
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.addInitScript(() => {
    try { localStorage.setItem('nl-popup-ts', String(Date.now())); } catch {}
  });
  await page.route('https://subscribe.davidpd89.workers.dev/**', route => route.fulfill({
    status: 201,
    contentType: 'application/json',
    body: JSON.stringify({ ok: true, state: 'pending_confirmation' })
  }));
  const response = await page.goto(ORIGIN + PATH, { waitUntil: 'domcontentloaded' });
  assert.ok(response?.ok(), `${PATH}: página no disponible`);
  const form = page.locator('#newsletter-form-fragmento');
  await form.waitFor({ state: 'visible' });
  await form.locator('input[type="email"]').fill('qa-confirmacion@example.com');
  await form.locator('[type="submit"]').click();
  await form.getByText(/Revisa tu correo/i).waitFor();
  const result = await form.evaluate(el => {
    const message = [...el.querySelectorAll('*')].find(node => node.children.length === 0 && /Revisa tu correo/i.test(node.textContent || ''));
    if (!message) return { exists: false, announced: false };
    const live = message.closest('[role="status"], [role="alert"], [aria-live]');
    const focused = document.activeElement === message || message.contains(document.activeElement);
    return { exists: true, announced: Boolean(live) || focused };
  });
  assert.ok(result.exists, `${PATH}: falta el resultado visible de suscripción`);
  assert.ok(result.announced, `${PATH}: el resultado se muestra, pero no dispone de región viva ni foco accesible`);
  await context.close();
} finally {
  await browser.close();
}
console.log('newsletter-result-announcement-browser: PASS');
