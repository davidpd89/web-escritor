import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

try {
  for (const route of ['/asistente/', '/asistente/embed.html']) {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    const failures = [];
    const checked = [];
    page.on('response', response => {
      const request = response.request();
      const url = new URL(response.url());
      if (url.origin !== origin || !['stylesheet', 'script', 'image', 'font'].includes(request.resourceType())) return;
      if (url.pathname.startsWith('/pagefind/')) return;
      checked.push(url.pathname);
      if (!response.ok()) failures.push(`${url.pathname}: HTTP ${response.status()}`);
    });
    page.on('requestfailed', request => {
      const url = new URL(request.url());
      if (url.origin === origin && ['stylesheet', 'script', 'image', 'font'].includes(request.resourceType()) && !url.pathname.startsWith('/pagefind/')) failures.push(`${url.pathname}: ${request.failure()?.errorText}`);
    });
    const documentResponse = await page.goto(`${origin}${route}`, { waitUntil: 'networkidle' });
    assert.equal(documentResponse?.status(), 200, `${route}: documento HTTP`);
    await page.locator('[data-assistant-query]').waitFor({ state: 'visible' });
    assert(checked.some(path => path.endsWith('/assistant.css')), `${route}: assistant.css no se ha solicitado`);
    assert(checked.some(path => path.endsWith('/assistant.js')), `${route}: assistant.js no se ha solicitado`);
    assert.deepEqual(failures, [], `${route}: recursos críticos fallidos`);
    await context.close();
  }
} finally {
  await browser.close();
}
console.log('assistant-critical-resources: OK');