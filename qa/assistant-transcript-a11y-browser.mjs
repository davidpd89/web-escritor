import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
try {
  for (const path of ['/asistente/', '/asistente/embed.html']) {
    const page = await browser.newPage();
    await page.route('**/*', r => new URL(r.request().url()).origin === origin ? r.continue() : r.abort());
    await page.goto(origin + path);
    const log = page.locator('[data-assistant-log]');
    assert.equal(await log.count(), 1, path);
    assert.equal(await log.getAttribute('role'), 'log', path);
    assert.equal(await log.getAttribute('aria-live'), 'polite', path);
    assert.match(await log.getAttribute('aria-label') || '', /conversación/i, path);
    const welcome = log.locator('.assistant-message--assistant').first();
    assert.equal(await welcome.getAttribute('aria-label'), 'Asistente', `${path}: bienvenida sin autor`);
    await page.locator('[data-assistant-query]').fill('¿Qué es Noveris?');
    await page.locator('[data-assistant-submit]').click();
    await page.waitForFunction(() => document.querySelector('[data-assistant-form]')?.getAttribute('aria-busy') === 'false');
    assert.equal(await log.locator('.assistant-message--user').last().getAttribute('aria-label'), 'Tú');
    assert.equal(await log.locator('.assistant-message--assistant').last().getAttribute('aria-label'), 'Asistente');
    assert.equal(await page.locator('[data-assistant-status]').getAttribute('role'), 'status');
    await page.close();
  }
} finally { await browser.close(); }
console.log('assistant-transcript-a11y: OK');
