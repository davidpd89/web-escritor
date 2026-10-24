import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
try {
  const context = await browser.newContext();
  await context.route('**/*', r => new URL(r.request().url()).origin === new URL(BASE).origin ? r.continue() : r.abort());
  const page = await context.newPage();
  await page.goto(BASE + '/cuaderno/');
  const data = await page.evaluate(() => {
    const feature = document.querySelector('.cuaderno-feature h2 a');
    const ledger = [...document.querySelectorAll('.cuaderno-ledger > .cuaderno-entry')];
    return {
      counter: Number(document.querySelector('.cuaderno-masthead__folio strong')?.textContent),
      links: [feature, ...ledger.map(entry => entry.querySelector('h3 a'))].map(a => ({ href: a?.getAttribute('href'), text: a?.textContent.trim() })),
      indexes: [...document.querySelectorAll('.cuaderno-entry__index')].map(el => Number(el.textContent.trim()))
    };
  });
  assert.equal(data.counter, data.links.length, 'Contador editorial desincronizado');
  assert.equal(new Set(data.links.map(x => x.href)).size, data.links.length, 'Destinos repetidos');
  assert.deepEqual(data.indexes, Array.from({ length: data.links.length - 1 }, (_, i) => i + 2));
  for (const item of data.links) {
    assert.ok(item.href?.startsWith('/') && item.text?.length > 5);
    const response = await context.request.get(BASE + item.href);
    assert.equal(response.status(), 200, item.href);
    const html = await response.text();
    assert.match(html, /<main\b/i, item.href);
    assert.match(html, /<h1\b/i, item.href);
    assert.doesNotMatch(html, /<meta[^>]+name=['"]robots['"][^>]+content=['"]noindex/i, `${item.href}: contenido retirado en archivo`);
  }
  await context.close();
  console.log('PASS Cuaderno archive traceability');
} finally { await browser.close(); }
