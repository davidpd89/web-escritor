import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const O = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  let posts = 0;
  await page.route('**/*', r => new URL(r.request().url()).origin === O ? r.continue() : r.abort());
  await page.route('**/assets/assistant-config.js', r => r.fulfill({ status: 200, contentType: 'application/javascript', body: 'export const ASSISTANT_PUBLIC_CONFIG=Object.freeze({protocolVersion:1,remoteEnabled:true,assistantUrl:"/api/assistant",configUrl:"/api/assistant/config",turnstileSiteKey:"",queryMinLength:2,queryMaxLength:500});' }));
  await page.route('**/api/assistant/config', r => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ protocol_version: 1, ok: true, enabled: true, turnstile_site_key: 'qa-key' }) }));
  await page.route('https://challenges.cloudflare.com/turnstile/v0/api.js*', r => r.fulfill({ status: 200, contentType: 'application/javascript', body: 'globalThis.turnstile={render(_el,opts){globalThis.__turnstileOptions=opts;return "qa"},execute(){},reset(){}};' }));
  await page.route('**/api/assistant', r => { posts++; return r.fulfill({ status: 200, contentType: 'application/json', body: '{}' }); });
  await page.goto(`${O}/asistente/`, { waitUntil: 'load' });
  await page.locator('[data-assistant-query]').fill('pregunta remota desconocida 827361');
  await page.locator('[data-assistant-submit]').click();
  await page.waitForFunction(() => Boolean(globalThis.__turnstileOptions));
  await page.locator('[data-assistant-stop]').click();
  assert.equal(await page.locator('[data-assistant-form]').getAttribute('aria-busy'), 'false');
  await page.evaluate(() => globalThis.__turnstileOptions.callback('qa-token-tardio'));
  await page.waitForTimeout(100);
  assert.equal(posts, 0, 'cancelled request sent after late token');
  assert.equal(await page.locator('[data-assistant-form]').getAttribute('aria-busy'), 'false');
  assert.equal(await page.locator('[data-pending="true"]').count(), 0);
} finally {
  await browser.close();
}
console.log('PASS assistant late Turnstile token cancellation');
