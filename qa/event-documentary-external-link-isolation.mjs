import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.EVENTOS_BASE_URL || process.env.FERIAS_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  for (const route of ['/eventos.html', '/ferias.html']) {
    const page = await browser.newPage();
    try {
      const response = await page.goto(new URL(route, BASE).href, { waitUntil: 'load' });
      assert.ok(response?.ok(), `${route}: HTTP ${response?.status()}`);
      const links = await page.locator('main a[href]').evaluateAll(nodes => nodes.map(a => ({ href: a.href, raw: a.getAttribute('href'), target: a.target, rel: a.rel.toLowerCase().split(/\s+/), handlers: [...a.attributes].filter(x => /^on/i.test(x.name)).map(x => x.name) })));
      assert.ok(links.length > 0, `${route}: no se encontraron enlaces editoriales`);
      let external = 0;
      for (const link of links) {
        const url = new URL(link.href);
        assert.deepEqual(link.handlers, [], `${route}: atributo ejecutable en ${link.raw}`);
        assert.ok(!['javascript:', 'data:', 'vbscript:'].includes(url.protocol), `${route}: protocolo peligroso ${link.raw}`);
        if (url.origin === 'https://davidportodiaz.com' || url.origin === new URL(BASE).origin) continue;
        if (url.protocol === 'mailto:' || url.protocol === 'tel:') continue;
        external++;
        assert.equal(url.protocol, 'https:', `${route}: enlace externo no HTTPS: ${link.raw}`);
        if (link.target === '_blank') {
          assert.ok(link.rel.includes('noopener'), `${route}: falta noopener en ${link.raw}`);
          assert.ok(link.rel.includes('noreferrer'), `${route}: falta noreferrer en ${link.raw}`);
        }
      }
      if (route === '/ferias.html') assert.ok(external > 0, `${route}: no se analizaron enlaces documentales externos`);
    } finally { await page.close(); }
  }
} finally { await browser.close(); }
console.log('event documentary external link isolation: OK');
