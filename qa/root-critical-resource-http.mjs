import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = (process.env.SITE_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const browser = await chromium.launch({ headless: true });

try {
  for (const seen of [false, true]) {
    const context = await browser.newContext();
    await context.addInitScript(value => {
      try {
        if (value) sessionStorage.setItem('dp-intro-seen', '1');
        else sessionStorage.removeItem('dp-intro-seen');
      } catch {}
    }, seen);
    const page = await context.newPage();
    const failures = [];
    page.on('response', response => {
      const request = response.request();
      const url = new URL(response.url());
      if (url.origin !== new URL(BASE).origin) return;
      if (!['stylesheet', 'script', 'image'].includes(request.resourceType())) return;
      if (response.status() >= 400) failures.push(`${url.pathname}: HTTP ${response.status()}`);
    });
    page.on('requestfailed', request => {
      const url = new URL(request.url());
      if (url.origin === new URL(BASE).origin && ['stylesheet', 'script', 'image'].includes(request.resourceType())) {
        failures.push(`${url.pathname}: ${request.failure()?.errorText || 'fallo de red'}`);
      }
    });
    const response = await page.goto(`${BASE}/`, { waitUntil: 'load' });
    assert.equal(response?.status(), 200, `Portada, intro vista=${seen}: respuesta HTTP inesperada`);
    await page.evaluate(async () => {
      await Promise.all([...document.images].filter(img => img.loading !== 'lazy').map(img => img.decode().catch(() => null)));
    });
    assert.deepEqual(failures, [], `Portada, intro vista=${seen}: recursos locales fallidos: ${failures.join('; ')}`);
    await context.close();
  }
  console.log('PASS: recursos locales de portada en ambos estados de introducción');
} finally {
  await browser.close();
}
