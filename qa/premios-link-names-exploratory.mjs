import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.IDENTITY_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  const page = await browser.newPage({ viewport: { width: 390, height: 900 } });
  const response = await page.goto(origin + '/premios.html', { waitUntil: 'load' });
  assert.ok(response?.ok());
  const links = await page.locator('main a[href]').evaluateAll(nodes => nodes.map(node => ({
    href: node.getAttribute('href'),
    name: (node.getAttribute('aria-label') || node.getAttribute('aria-labelledby') || node.innerText || node.textContent || '').trim().replace(/\s+/g, ' '),
    hidden: node.hidden || node.closest('[hidden], [aria-hidden="true"]') !== null
  })));
  assert.ok(links.length > 0, 'No hay enlaces en el contenido principal');
  for (const link of links) {
    if (link.hidden) continue;
    assert.ok(link.name.length >= 3, `Enlace sin nombre accesible: ${link.href}`);
    assert.notEqual(link.href, '#', 'Enlace sin destino');
  }
  const sources = await page.locator('[data-award-source]').evaluateAll(nodes => nodes.map(node => ({
    name: (node.getAttribute('aria-label') || node.textContent || '').trim().replace(/\s+/g, ' '),
    href: node.href
  })));
  assert.ok(sources.length >= 3);
  assert.ok(sources.every(source => source.name.length >= 3));
  console.log(`PASS: ${links.length} enlaces y ${sources.length} fuentes examinados`);
} finally {
  await browser.close();
}
