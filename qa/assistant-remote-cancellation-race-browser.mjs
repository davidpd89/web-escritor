import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
let release;
const gate = new Promise(resolve => { release = resolve; });
try {
  const page = await browser.newPage();
  await page.route('**/*', r => new URL(r.request().url()).origin === origin ? r.continue() : r.abort());
  await page.route('**/assets/assistant-config.js', r => r.fulfill({
    contentType: 'application/javascript',
    body: 'export const ASSISTANT_PUBLIC_CONFIG=Object.freeze({protocolVersion:1,remoteEnabled:true,assistantUrl:"/api/assistant",configUrl:"/api/assistant/config",turnstileSiteKey:"",queryMinLength:2,queryMaxLength:500});',
  }));
  await page.route('**/api/assistant/config', r => r.fulfill({
    contentType: 'application/json',
    body: JSON.stringify({ protocol_version: 1, ok: true, enabled: true, turnstile_site_key: 'qa-key' }),
  }));
  await page.route('https://challenges.cloudflare.com/turnstile/v0/api.js*', r => r.fulfill({
    contentType: 'application/javascript',
    body: 'globalThis.turnstile={render(_el,o){globalThis.__qa=o;return "id"},execute(){queueMicrotask(()=>globalThis.__qa.callback("token"))},reset(){}};',
  }));
  await page.route('**/api/assistant', async r => {
    if (r.request().method() !== 'POST') return r.continue();
    await gate;
    try {
      await r.fulfill({ contentType: 'application/json', body: JSON.stringify({
        protocol_version: 1, ok: true, abstained: false,
        answer: 'RESPUESTA_OBSOLETA [author]',
        sources: [{ id: 'author', title: 'Autor', url: '/autor.html' }],
      }) });
    } catch { /* La petición puede estar abortada. */ }
  });
  await page.goto(origin + '/asistente/');
  await page.locator('[data-assistant-query]').fill('Consulta remota desconocida XYZ987');
  const posted = page.waitForRequest(r => r.url().endsWith('/api/assistant') && r.method() === 'POST');
  await page.locator('[data-assistant-submit]').click();
  await posted;
  await page.locator('[data-assistant-stop]').click();
  release();
  await page.waitForFunction(() => document.querySelector('[data-assistant-form]')?.getAttribute('aria-busy') === 'false');
  assert.equal(await page.locator('[data-pending="true"]').count(), 0);
  assert.doesNotMatch(await page.locator('[data-assistant-log]').innerText(), /RESPUESTA_OBSOLETA/);
  await page.locator('[data-assistant-query]').fill('¿Qué es Noveris?');
  await page.locator('[data-assistant-submit]').click();
  await page.waitForFunction(() => document.querySelector('[data-assistant-form]')?.getAttribute('aria-busy') === 'false');
  assert.match(await page.locator('.assistant-message--assistant').last().innerText(), /Noveris/i);
} finally { release?.(); await browser.close(); }
console.log('assistant-remote-cancellation-race: OK');
