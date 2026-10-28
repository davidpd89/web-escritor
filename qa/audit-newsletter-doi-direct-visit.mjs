import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
await context.route(/^https?:/, r => r.request().url().startsWith(BASE) ? r.continue() : r.abort());
const page = await context.newPage();
try {
  const response = await page.goto(BASE + '/gracias-suscripcion/', { waitUntil: 'load' });
  assert.equal(response.status(), 200);
  const stored = await page.evaluate(() => localStorage.getItem('nl-subscribed'));
  assert.notEqual(stored, '1', 'Una URL pública marca la suscripción como confirmada sin prueba DOI');
} finally {
  await browser.close();
}
console.log('audit-newsletter-doi-direct-visit: PASS');