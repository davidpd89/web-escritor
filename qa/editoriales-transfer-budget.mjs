import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const MAX_BYTES = 1536 * 1024;
const MAX_REQUESTS = 80;
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  const ownOrigin = new URL(ORIGIN).origin;
  const responses = [];
  page.on('response', response => {
    if (new URL(response.url()).origin === ownOrigin) responses.push(response);
  });
  const navigation = await page.goto(`${ORIGIN}/editoriales/`, { waitUntil: 'networkidle' });
  assert.equal(navigation?.ok(), true, '/editoriales/: documento inicial no disponible');
  await page.evaluate(() => document.fonts.ready);
  let transferred = 0;
  const resources = [];
  for (const response of responses) {
    const sizes = await response.request().sizes();
    const bytes = sizes.responseBodySize + sizes.responseHeadersSize;
    transferred += bytes;
    resources.push({ url: response.url(), bytes });
  }
  resources.sort((a, b) => b.bytes - a.bytes);
  assert.ok(transferred <= MAX_BYTES, `/editoriales/: transferencia ${transferred} B supera ${MAX_BYTES} B. Mayores recursos: ${JSON.stringify(resources.slice(0, 5))}`);
  assert.ok(responses.length <= MAX_REQUESTS, `/editoriales/: ${responses.length} peticiones superan ${MAX_REQUESTS}`);
  const visible = await page.locator('[data-editorial-card]:visible').count();
  assert.ok(visible > 0, '/editoriales/: presupuesto medido sin resultados visibles');
  console.log(`editoriales-transfer-budget: PASS (${transferred} B, ${responses.length} peticiones)`);
} finally {
  await browser.close();
}