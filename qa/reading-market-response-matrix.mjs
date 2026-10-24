import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import { execFileSync } from 'node:child_process';

const base = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const dir = '.ci/reading-market-response-matrix';
await fs.mkdir(dir, { recursive: true });
execFileSync(process.env.PYTHON || 'python', ['tests/test-reading-catalogue.py', '--browser-fixture', `${dir}/fixture.json`]);
const fixture = JSON.parse(await fs.readFile(`${dir}/fixture.json`, 'utf8'));
const browser = await chromium.launch({ headless: true });
const scenarios = [
  { name: 'http-503', run: route => route.fulfill({ status: 503, body: 'Unavailable' }) },
  { name: 'invalid-json', run: route => route.fulfill({ contentType: 'application/json', body: '{invalid' }) },
  { name: 'empty-object', run: route => route.fulfill({ json: {} }) },
  { name: 'null-arrays', run: route => route.fulfill({ json: { schema_version: 1, offers: null, ratings: null } }) },
  { name: 'network-abort', run: route => route.abort('failed') }
];
try {
  for (const scenario of scenarios) {
    const context = await browser.newContext();
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await context.route('**/recomendaciones/', route => route.fulfill({ contentType: 'text/html', body: fixture.hub }));
    await context.route('**/assets/reading-market.json', scenario.run);
    await page.goto(`${base}/recomendaciones/`, { waitUntil: 'networkidle' });
    assert.equal(await page.locator('[data-catalogue-book]').count(), 2, scenario.name);
    assert.equal(await page.locator('[data-catalogue-book] h3 a[href]').count(), 2, scenario.name);
    assert.equal(await page.locator('[data-catalogue-book]:visible').count(), 2, scenario.name);
    assert.deepEqual(errors, [], scenario.name);
    await context.close();
  }
} finally {
  await browser.close();
}
