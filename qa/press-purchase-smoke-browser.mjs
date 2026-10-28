import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const browser = await chromium.launch({ headless: true });

try {
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const response = await page.goto(ORIGIN + '/prensa.html', { waitUntil: 'domcontentloaded' });
  assert.ok(response?.ok(), `/prensa.html: HTTP ${response?.status()}`);

  const links = page.locator('a[href^="https://amzn.to/"]');
  assert.ok(await links.count() > 0, '/prensa.html: no existen enlaces comerciales Amazon');

  let accessible = 0;
  for (const link of await links.all()) {
    if (!await link.isVisible()) continue;
    const href = await link.getAttribute('href');
    const url = new URL(href);
    assert.equal(url.protocol, 'https:', `/prensa.html: protocolo de compra inválido: ${href}`);
    assert.equal(url.hostname, 'amzn.to', `/prensa.html: autoridad comercial inesperada: ${href}`);
    assert.ok(!url.username && !url.password, `/prensa.html: enlace de compra con credenciales: ${href}`);
    const label = ((await link.getAttribute('aria-label')) || await link.innerText()).trim();
    assert.ok(label.length > 0, `/prensa.html: enlace comercial sin nombre accesible: ${href}`);
    await link.focus();
    assert.ok(await link.evaluate(el => document.activeElement === el), `/prensa.html: enlace de compra sin foco: ${href}`);
    accessible++;
  }

  assert.ok(accessible > 0, '/prensa.html: ningún enlace comercial visible y enfocable');
  assert.deepEqual(errors, [], `/prensa.html: errores JavaScript: ${errors.join('; ')}`);
  console.log(`OK: ${accessible} enlaces comerciales accesibles`);
} finally {
  await browser.close();
}
