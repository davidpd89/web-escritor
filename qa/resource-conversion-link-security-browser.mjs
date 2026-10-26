import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const routes = ['/recursos/ficha-historia-objeto-heredado/'];
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

try {
  for (const route of routes) {
    const context = await browser.newContext();
    const page = await context.newPage();
    const response = await page.goto(new URL(route, BASE).href, { waitUntil: 'domcontentloaded' });
    assert.ok(response?.ok(), `${route}: documento no disponible`);

    const links = await page.locator('a[href]').evaluateAll(nodes => nodes.map(node => ({
      href: node.getAttribute('href'),
      target: node.getAttribute('target'),
      rel: node.getAttribute('rel') || '',
      label: node.getAttribute('aria-label') || node.textContent.trim(),
      external: (() => { try { return new URL(node.href).origin !== location.origin; } catch { return false; } })()
    })).filter(link => link.external));

    assert.ok(links.some(link => /comprar/i.test(link.label)), `${route}: no se encontró el enlace comercial publicado`);
    for (const link of links) {
      const url = new URL(link.href, BASE);
      assert.ok(['http:', 'https:'].includes(url.protocol), `${route}: destino externo con protocolo inseguro: ${link.href}`);
      if (link.target === '_blank') {
        const tokens = link.rel.toLowerCase().split(/\s+/);
        assert.ok(tokens.includes('noopener') || tokens.includes('noreferrer'), `${route}: enlace ${link.href} abre pestaña sin aislamiento explícito`);
      }
    }

    const buy = page.locator('a.header-buy').first();
    assert.ok(await buy.count(), `${route}: falta acción comercial en la cabecera`);
    const destination = await buy.getAttribute('href');
    assert.ok(/^https:\/\//i.test(destination), `${route}: compra no utiliza HTTPS: ${destination}`);
    assert.equal(await buy.getAttribute('target'), '_blank', `${route}: la compra debe conservar la página de origen`);
    await context.close();
  }
  console.log('PASS resource conversion link security');
} finally {
  await browser.close();
}
