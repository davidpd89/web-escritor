import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
await context.route(/^https?:/, r => r.request().url().startsWith(BASE) ? r.continue() : r.abort());
const page = await context.newPage();
await page.route('https://subscribe.davidpd89.workers.dev/**', r => r.fulfill({
  status: 201,
  contentType: 'application/json',
  body: '{"ok":true,"state":"pending_confirmation"}'
}));
try {
  await page.goto(BASE + '/fragmento/', { waitUntil: 'load' });
  const form = page.locator('#newsletter-form-fragmento');
  await form.locator('input[type="email"]').fill('accessible@example.com');
  await form.locator('[type="submit"]').click();
  await page.waitForFunction(() => document.querySelector('#newsletter-form-fragmento')?.textContent?.includes('Revisa tu correo'));
  const announced = await form.evaluate(el => {
    const result = el.querySelector('.quiz-subscribe-ok');
    if (!result) return false;
    const live = result.closest('[role="status"], [role="alert"], [aria-live="polite"], [aria-live="assertive"]');
    return Boolean(live || result.contains(document.activeElement) || result === document.activeElement);
  });
  assert(announced, 'La confirmación se inserta en el DOM sin anuncio ni foco accesible');
} finally {
  await browser.close();
}
console.log('audit-newsletter-success-announcement: PASS');