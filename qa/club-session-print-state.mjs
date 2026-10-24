import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
await context.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
await context.addInitScript(() => {
  window.__clubPrints = [];
  window.print = () => window.__clubPrints.push(document.querySelector('[data-club-session-output]').innerText);
});
const page = await context.newPage();

try {
  await page.goto(`${origin}/clubes-de-lectura/preparar-sesion/`, { waitUntil: 'load' });
  await page.locator('[data-club-session-print]').click();
  assert.deepEqual(await page.evaluate(() => window.__clubPrints), []);
  await page.selectOption('#club-duration', '90');
  await page.locator('[data-club-session-form] button[type=submit]').click();
  const first = await page.locator('[data-club-session-output]').innerText();
  await page.locator('[data-club-session-print]').click();
  await page.locator('[data-club-session-alt]').click();
  const second = await page.locator('[data-club-session-output]').innerText();
  assert.notEqual(first, second);
  await page.locator('[data-club-session-print]').click();
  assert.deepEqual(await page.evaluate(() => window.__clubPrints), [first, second]);
} finally {
  await browser.close();
}
console.log('club-session-print-state: OK');