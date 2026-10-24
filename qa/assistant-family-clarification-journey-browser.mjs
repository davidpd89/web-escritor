import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const O = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const cases = [
  { label: 'Samuel', href: '/fragmento/' },
  { label: 'Las manecillas', href: '/las-manecillas-del-recuerdo/fragmentos/' }
];
const browser = await chromium.launch({ headless: true });
try {
  for (const c of cases) {
    const page = await browser.newPage();
    await page.route('**/*', r => new URL(r.request().url()).origin === O ? r.continue() : r.abort());
    await page.goto(`${O}/asistente/`, { waitUntil: 'load' });
    const query = page.locator('[data-assistant-query]');
    const send = page.locator('[data-assistant-submit]');
    await query.fill('Quiero leer un fragmento');
    await send.click();
    await page.locator('.assistant-reply-chip').first().waitFor();
    assert.equal(await page.locator('.assistant-reply-chip').count(), 2);
    await page.locator('.assistant-reply-chip').filter({ hasText: c.label }).first().click();
    await page.waitForFunction(() => document.querySelector('[data-assistant-form]')?.getAttribute('aria-busy') === 'false');
    const selected = page.locator('.assistant-message--assistant').last();
    assert.deepEqual(await selected.locator('.assistant-message__sources a').evaluateAll(a => a.map(x => x.getAttribute('href'))), [c.href]);
    await query.fill('¿Qué herramientas gratuitas hay para escritores?');
    await send.click();
    await page.waitForFunction(() => document.querySelector('[data-assistant-form]')?.getAttribute('aria-busy') === 'false');
    assert.deepEqual(await page.locator('.assistant-message--assistant').last().locator('.assistant-message__sources a').evaluateAll(a => a.map(x => x.getAttribute('href'))), ['/herramientas/']);
    await page.close();
  }
} finally {
  await browser.close();
}
console.log('PASS assistant clarification journeys');
