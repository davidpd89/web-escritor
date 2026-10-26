import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || process.env.SITE_BASE_URL || 'http://127.0.0.1:4173').replace(/\/$/, '');
const ROUTES = ['/accesibilidad/', '/editoriales/', '/herramientas/', '/recomendaciones/'];
const browser = await chromium.launch({ headless: true });

try {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const css = new Set();
  for (const route of ROUTES) {
    const page = await context.newPage();
    try {
      const response = await page.goto(`${ORIGIN}${route}`, { waitUntil: 'domcontentloaded' });
      assert.equal(response?.status(), 200, `${route}: HTTP ${response?.status()}`);
      const urls = await page.locator('link[rel="stylesheet"][href]').evaluateAll(nodes => nodes.map(n => n.href).filter(h => new URL(h).origin === location.origin));
      assert.ok(urls.length > 0, `${route}: ninguna hoja de estilos local declarada`);
      urls.forEach(url => css.add(url));
    } finally {
      await page.close();
    }
  }
  const urls = [...css];
  assert.ok(urls.length >= 4, `Inventario CSS inesperadamente pequeño: ${urls.length}`);
  const jobs = Array.from({ length: 3 }, () => urls).flat();
  const results = await Promise.all(jobs.map(async (url, index) => {
    const response = await context.request.get(url, { timeout: 15000 });
    const body = await response.body();
    return { url, index, status: response.status(), type: response.headers()['content-type'] || '', length: body.length };
  }));
  for (const r of results) {
    assert.equal(r.status, 200, `${r.url} petición ${r.index}: HTTP ${r.status}`);
    assert.ok(r.length > 0, `${r.url} petición ${r.index}: CSS vacío`);
    assert.match(r.type, /text\/css/i, `${r.url} petición ${r.index}: MIME ${r.type}`);
  }
  await context.close();
  console.log(`PASS concurrent CSS: ${results.length} responses, ${urls.length} resources`);
} finally {
  await browser.close();
}