import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const hosts = new Set(['goodreads.com', 'www.goodreads.com', 'hardcover.app', 'www.hardcover.app', 'books.google.com']);
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

try {
  for (const width of [320, 360, 390]) {
    const context = await browser.newContext({ viewport: { width, height: 800 }, isMobile: true, hasTouch: true });
    const page = await context.newPage();
    const response = await page.goto(new URL('/recomendaciones/', BASE).href, { waitUntil: 'domcontentloaded' });
    assert.ok(response?.ok(), `/recomendaciones/ ${width}px: respuesta ${response?.status()}`);
    await page.locator('[data-rating-book]').first().waitFor({ state: 'attached' });
    await page.waitForFunction(() => [...document.querySelectorAll('[data-rating-book]')].some(box => box.querySelector('a[href]')));
    const links = await page.locator('[data-rating-book] a[href]').evaluateAll(nodes => nodes.map(a => ({ href: a.href, target: a.target, rel: a.rel, text: a.textContent.trim(), label: a.getAttribute('aria-label') })));
    assert.ok(links.length, `/recomendaciones/ ${width}px: no hay enlaces de valoración renderizados`);
    for (const link of links) {
      const url = new URL(link.href);
      assert.equal(url.protocol, 'https:', `/recomendaciones/ ${width}px: valoración no HTTPS ${link.href}`);
      assert.ok(hosts.has(url.hostname), `/recomendaciones/ ${width}px: proveedor inesperado ${link.href}`);
      if (link.target === '_blank') assert.match(link.rel, /(?:^|\s)(?:noopener|noreferrer)(?:\s|$)/i, `/recomendaciones/ ${width}px: valoración sin aislamiento ${link.href}`);
      assert.ok(link.text || link.label, `/recomendaciones/ ${width}px: valoración sin nombre ${link.href}`);
    }
    await context.close();
  }
} finally {
  await browser.close();
}
console.log('PASS postmerge mobile rating link security');
