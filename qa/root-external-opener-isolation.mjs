import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = (process.env.SITE_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const browser = await chromium.launch({ headless: true });

try {
  const page = await browser.newPage();
  const response = await page.goto(`${BASE}/`, { waitUntil: 'load' });
  assert.equal(response?.status(), 200, 'Portada: navegación HTTP fallida');
  await page.locator('html[data-home-editorial-v3=true]').waitFor({ state: 'attached' });
  const links = await page.locator('a[href][target=_blank]').evaluateAll(nodes => nodes.map(a => ({
    href: a.href,
    rel: a.rel,
    external: new URL(a.href).origin !== location.origin
  })).filter(x => x.external));
  assert.ok(links.length, 'Portada: no se encontraron enlaces externos para verificar el aislamiento');
  for (const link of links) {
    const rel = new Set(link.rel.toLowerCase().split(/\s+/));
    assert.ok(rel.has('noopener') || rel.has('noreferrer'), `Portada: enlace externo sin aislamiento explícito: ${link.href} (rel=${link.rel})`);
  }
  console.log(`PASS: ${links.length} enlaces externos aislados en portada`);
} finally {
  await browser.close();
}
