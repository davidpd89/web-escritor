import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import { execFileSync } from 'node:child_process';

const base = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const dir = '.ci/reading-rating-url-boundaries';
await fs.mkdir(dir, { recursive: true });
execFileSync(process.env.PYTHON || 'python', ['tests/test-reading-catalogue.py', '--browser-fixture', `${dir}/fixture.json`]);
const fixture = JSON.parse(await fs.readFile(`${dir}/fixture.json`, 'utf8'));
const browser = await chromium.launch({ headless: true });
const now = new Date('2026-10-20T12:00:00Z');
const stamp = { actualizado_en: '2026-10-20T11:00:00Z', caduca_en: '2026-10-21T11:00:00Z' };
try {
  for (const candidate of [
    { fuente: 'goodreads', url: 'https://www.goodreads.com/book/show/123evil' },
    { fuente: 'goodreads', url: 'https://www.goodreads.com/book/show/123/../../user' },
    { fuente: 'google_books', url: 'https://books.google.com/books?id=ABCD&redirect=https://evil.invalid' },
    { fuente: 'hardcover', url: 'https://hardcover.app/books/book-one/../account' }
  ]) {
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.clock.install({ time: now });
    await context.route('**/recomendaciones/', route => route.fulfill({ contentType: 'text/html', body: fixture.hub }));
    await context.route('**/assets/reading-market.json', route => route.fulfill({ json: {
      schema_version: 1, offers: [], ratings: [{ ...stamp, libro_id: 'contrato-uno', puntuacion: 4.5, numero_valoraciones: 100, ...candidate }]
    } }));
    await page.goto(`${base}/recomendaciones/`, { waitUntil: 'networkidle' });
    const hrefs = await page.locator('[data-rating-book] a').evaluateAll(links => links.map(a => a.href));
    assert(!hrefs.includes(candidate.url), `URL potencialmente ambigua aceptada: ${candidate.url}`);
    await context.close();
  }
} finally {
  await browser.close();
}
