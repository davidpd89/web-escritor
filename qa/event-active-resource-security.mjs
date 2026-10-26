import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.EVENTOS_BASE_URL || process.env.FERIAS_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  for (const route of ['/eventos.html', '/ferias.html']) {
    const page = await browser.newPage();
    try {
      const response = await page.goto(new URL(route, BASE).href, { waitUntil: 'load' });
      assert.ok(response?.ok(), `${route}: documento no disponible`);
      const resources = await page.evaluate(() => {
        const selectors = ['script[src]', 'link[rel=stylesheet][href]', 'iframe[src]', 'object[data]', 'embed[src]', 'form[action]'];
        return selectors.flatMap(selector => [...document.querySelectorAll(selector)].map(el => ({ tag: el.tagName, url: el.getAttribute('src') || el.getAttribute('href') || el.getAttribute('data') || el.getAttribute('action') })));
      });
      assert.ok(resources.length > 0, `${route}: no se inspeccionaron recursos activos`);
      for (const item of resources) {
        const raw = item.url.trim();
        if (!raw || raw.startsWith('#')) continue;
        assert.ok(!raw.startsWith('//'), `${route}: recurso con protocolo implícito ${raw}`);
        const resolved = new URL(raw, new URL(route, BASE));
        assert.ok(['https:', 'http:'].includes(resolved.protocol), `${route}: protocolo activo inesperado ${item.tag} ${raw}`);
        assert.ok(resolved.protocol === 'https:' || resolved.origin === new URL(BASE).origin, `${route}: recurso HTTP externo ${item.tag} ${raw}`);
      }
      const handlers = await page.locator('main *').evaluateAll(nodes => nodes.flatMap(el => [...el.attributes].filter(a => /^on[a-z]+$/i.test(a.name)).map(a => `${el.tagName}[${a.name}]`)));
      assert.deepEqual(handlers, [], `${route}: atributos ejecutables en contenido editorial: ${handlers.join(', ')}`);
    } finally { await page.close(); }
  }
} finally { await browser.close(); }
console.log('event active resource security: OK');
