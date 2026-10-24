import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import { execFileSync } from 'node:child_process';

const base = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const dir = '.ci/reading-rating-expiry';
await fs.mkdir(dir, { recursive: true });
execFileSync(process.env.PYTHON || 'python', ['tests/test-reading-catalogue.py', '--browser-fixture', `${dir}/fixture.json`]);
const fixture = JSON.parse(await fs.readFile(`${dir}/fixture.json`, 'utf8'));
const browser = await chromium.launch({ headless: true });
try {
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.clock.install({ time: new Date('2026-10-20T12:00:00Z') });
  await context.route('**/recomendaciones/', route => route.fulfill({ contentType: 'text/html', body: fixture.hub }));
  await context.route('**/assets/reading-market.json', route => route.fulfill({ json: {
    schema_version: 1,
    offers: [],
    ratings: [{
      libro_id: 'contrato-uno',
      fuente: 'google_books',
      puntuacion: 4.8,
      numero_valoraciones: 120,
      url: 'https://books.google.com/books?id=TEST123',
      actualizado_en: '2026-10-20T11:00:00Z',
      caduca_en: '2026-10-20T13:00:00Z'
    }]
  } }));
  await page.goto(`${base}/recomendaciones/`, { waitUntil: 'networkidle' });
  const rating = page.locator('[data-rating-book="contrato-uno"]');
  await page.waitForFunction(() => document.querySelector('[data-rating-book="contrato-uno"]')?.textContent.includes('4,8'));
  assert.match(await rating.innerText(), /4,8/);
  await page.clock.fastForward(2 * 3600000);
  await page.evaluate(() => window.dispatchEvent(new Event('pageshow')));
  assert.doesNotMatch(await rating.innerText(), /4,8/, 'La valoración caducada continúa visible');
  await context.close();
} finally {
  await browser.close();
}
