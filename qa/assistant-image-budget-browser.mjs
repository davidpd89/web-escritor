import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
const maxBytes = 250 * 1024;

try {
  for (const route of ['/asistente/', '/asistente/embed.html']) {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    const images = [];
    page.on('response', async response => {
      if (response.request().resourceType() !== 'image') return;
      const url = new URL(response.url());
      if (url.origin !== origin) return;
      images.push(response);
    });
    await page.goto(`${origin}${route}`, { waitUntil: 'networkidle' });
    for (const response of images) {
      assert(response.ok(), `${route}: imagen ${response.url()} HTTP ${response.status()}`);
      const bytes = (await response.body()).byteLength;
      assert(bytes <= maxBytes, `${route}: imagen ${response.url()} ocupa ${bytes} bytes; máximo ${maxBytes}`);
    }
    const invalid = await page.locator('img').evaluateAll(elements => elements.filter(el => {
      const style = getComputedStyle(el);
      if (style.display === 'none' || style.visibility === 'hidden') return false;
      const rect = el.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0 && (!el.complete || el.naturalWidth <= 0 || el.naturalHeight <= 0);
    }).map(el => ({ src: el.currentSrc || el.src, width: el.naturalWidth, height: el.naturalHeight })));
    assert.deepEqual(invalid, [], `${route}: imágenes visibles sin dimensiones naturales`);
    await context.close();
  }
} finally {
  await browser.close();
}
console.log('assistant-image-budget: OK');