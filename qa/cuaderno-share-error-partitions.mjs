import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const routes = ['/cuaderno/que-es-el-portal-fantasy/', '/cuaderno/sistema-de-magia-noveris/'];
const browser = await chromium.launch({ headless: true });
try {
  for (const route of routes) for (const mode of ['abort', 'failure']) {
    const context = await browser.newContext();
    await context.route('**/*', r => new URL(r.request().url()).origin === new URL(BASE).origin ? r.continue() : r.abort());
    await context.addInitScript(mode => {
      localStorage.setItem('nl-popup-ts', String(Date.now()));
      window.__copies = 0;
      Object.defineProperty(navigator, 'share', { configurable: true, value: async () => { throw new DOMException('Rejected', mode === 'abort' ? 'AbortError' : 'NotAllowedError'); } });
      Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText: async () => { window.__copies++; throw new Error('Clipboard denied'); } } });
    }, mode);
    const page = await context.newPage();
    try {
      await page.goto(BASE + route);
      await page.locator('[data-share-url]').click();
      await page.waitForTimeout(100);
      const copies = await page.evaluate(() => window.__copies);
      const status = (await page.locator('#article-share-status').innerText()).trim();
      if (mode === 'abort') {
        assert.equal(copies, 0, `${route}: cancelación activó el portapapeles`);
        assert.equal(status, '', `${route}: cancelación anunció resultado`);
      } else {
        assert.equal(copies, 1, `${route}: fallback no ejecutado`);
        assert.match(status, /No se pudo copiar/i, `${route}: error no anunciado`);
      }
    } finally { await context.close(); }
  }
  console.log('PASS share error partitions');
} finally { await browser.close(); }
