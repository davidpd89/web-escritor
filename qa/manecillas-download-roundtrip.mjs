import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  const context = await browser.newContext({ acceptDownloads: true });
  await context.route('**/*', route => route.request().url().startsWith(origin) ? route.continue() : route.abort());
  const page = await context.newPage();
  await page.goto(`${origin}/las-manecillas-del-recuerdo/kindle/`);
  for (const format of ['epub', 'txt']) {
    const link = page.locator(`[data-sample-download="${format}"]`).last();
    const href = await link.getAttribute('href');
    assert(href.startsWith('/assets/downloads/manecillas/'));
    assert(href.endsWith(`.${format}`));
    assert.equal(await link.getAttribute('download'), '');
    const [download] = await Promise.all([page.waitForEvent('download'), link.click()]);
    assert(download.suggestedFilename().endsWith(`.${format}`));
    assert.equal(await download.failure(), null);
    const actual = fs.readFileSync(await download.path());
    const expected = fs.readFileSync(path.join(process.cwd(), href.slice(1)));
    assert.deepEqual(actual, expected, `Descarga corrupta: ${format}`);
    assert(actual.length > 1000, `Archivo sospechosamente vacío: ${format}`);
    assert.equal(page.url(), `${origin}/las-manecillas-del-recuerdo/kindle/`);
  }
  await context.close();
  console.log('manecillas-download-roundtrip: OK');
} finally {
  await browser.close();
}
