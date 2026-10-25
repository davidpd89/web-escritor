import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
const cases = [
  ['#club-duration', '90'],
  ['#club-kind', 'nonfiction'],
  ['#club-scope', 'partial'],
  ['#club-tone', 'deep']
];

try {
  for (const [selector, value] of cases) {
    const context = await browser.newContext();
    await context.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
    const page = await context.newPage();
    await page.goto(`${origin}/clubes-de-lectura/preparar-sesion/`, { waitUntil: 'load' });
    await page.locator('[data-club-session-form] button[type=submit]').click();
    const output = page.locator('[data-club-session-output]');
    const before = await output.innerText();
    await page.selectOption(selector, value);
    const after = await output.innerText();
    const status = await page.locator('[data-club-session-status]').innerText();
    const copyDisabled = await page.locator('[data-club-session-copy]').isDisabled();
    const printDisabled = await page.locator('[data-club-session-print]').isDisabled();
    const warned = /cambiado|modificado|actualiza|prepara de nuevo|pendiente/i.test(status);
    assert.ok(after !== before || warned || (copyDisabled && printDisabled), `${selector}=${value}: resultado obsoleto exportable sin advertencia`);
    await context.close();
  }
} finally {
  await browser.close();
}
console.log('club-session-stale-exports: OK');