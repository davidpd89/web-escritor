import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { once } from 'node:events';

const port = 43871;
const origin = `http://127.0.0.1:${port}`;
const server = spawn('python3', ['-m', 'http.server', String(port), '--bind', '127.0.0.1'], { stdio: 'ignore' });
const browser = await chromium.launch({ headless: true });

async function ready() {
  for (let i = 0; i < 50; i++) {
    try {
      const response = await fetch(`${origin}/fragmento/`);
      if (response.ok) return;
    } catch {}
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  throw new Error('Servidor local no disponible');
}

try {
  await ready();
  const context = await browser.newContext();
  await context.addInitScript(() => {
    window.__consentCalls = [];
    window.clarity = (...args) => window.__consentCalls.push(args);
    window.__ANALYTICS_CONSENT_GRACE_MS__ = 10000;
  });
  const page = await context.newPage();
  await page.goto(`${origin}/fragmento/`);
  const banner = page.locator('[data-analytics-consent-banner]');
  await banner.waitFor();
  await banner.getByRole('button', { name: 'Rechazo ayudarte' }).click();
  await assertStored('denied');
  await page.evaluate(() => {
    document.dispatchEvent(new Event('scroll', { bubbles: true }));
    document.body.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  });
  await assertStored('denied');
  await page.reload();
  await assertStored('denied');
  assert.equal(await banner.count(), 0, 'El rechazo persistido no debe mostrar otra vez el banner');
  const calls = await page.evaluate(() => window.__consentCalls);
  assert.equal(calls.some(([name, value]) => name === 'consentv2' && value?.analytics_Storage === 'granted'), false, 'Se comunicó una aceptación posterior al rechazo');
  console.log('assets-consent-rejection-persistence: OK');

  async function assertStored(expected) {
    const value = await page.evaluate(() => JSON.parse(localStorage.getItem('dp-analytics-consent') || 'null')?.value);
    assert.equal(value, expected);
  }
} finally {
  await browser.close();
  server.kill();
  if (server.exitCode === null) await Promise.race([once(server, 'exit'), new Promise(resolve => setTimeout(resolve, 1000))]);
}
