import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';

const BASE = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const registry = JSON.parse(fs.readFileSync('data/analytics-events.json', 'utf8'));
const names = new Map(registry.events.map(e => [e.name, e]));
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
  await page.evaluate(() => {
    window.__auditEvents = [];
    window._gcEvent = (name, label) => window.__auditEvents.push({ name, label });
  });
  const form = page.locator('#newsletter-form-fragmento');
  await form.locator('input[type="email"]').fill('analytics@example.com');
  await form.locator('[type="submit"]').click();
  await page.waitForFunction(() => document.querySelector('#newsletter-form-fragmento')?.textContent?.includes('Revisa tu correo'));
  const actual = await page.evaluate(() => window.__auditEvents.filter(e => e.name.startsWith('newsletter-')));
  assert.equal(actual.length, 1, 'Conversión duplicada o no emitida');
  const event = names.get(actual[0].name);
  assert(event, 'Evento dinámico ausente del registro: ' + actual[0].name);
  assert.equal(event.context, 'fragmento');
  assert.equal(event.action, 'newsletter_submit');
} finally {
  await browser.close();
}
console.log('audit-newsletter-event-registry-runtime: PASS');