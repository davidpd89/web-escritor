import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';

const browser = await chromium.launch({headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});
try {
  const page = await browser.newPage();
  await page.setContent(readFileSync('offline.html', 'utf8'));
  const result = await page.evaluate(() => {
    const retry = document.querySelector('[data-retry]');
    const back = document.querySelector('[data-back]');
    const status = document.querySelector('[data-status]');
    return {
      retryTag: retry?.tagName,
      retryType: retry?.getAttribute('type'),
      retryName: retry?.getAttribute('aria-label') || retry?.textContent.trim(),
      backTag: back?.tagName,
      backType: back?.getAttribute('type'),
      backName: back?.getAttribute('aria-label') || back?.textContent.trim(),
      statusRole: status?.getAttribute('role'),
      statusLive: status?.getAttribute('aria-live'),
      statusText: status?.textContent.trim(),
      heading: document.querySelector('#offline-title')?.textContent.trim()
    };
  });
  assert.equal(result.retryTag, 'BUTTON');
  assert.equal(result.retryType, 'button');
  assert(result.retryName);
  assert.equal(result.backTag, 'BUTTON');
  assert.equal(result.backType, 'button');
  assert(result.backName);
  assert.equal(result.statusRole, 'status');
  assert.equal(result.statusLive, 'polite');
  assert(result.statusText);
  assert(result.heading);
} finally {
  await browser.close();
}
console.log('PASS offline recovery accessibility');
