import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';
const ROOT = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const registry = JSON.parse(fs.readFileSync('data/content-registry.json', 'utf8'));
const groups = new Map();
for (const entry of registry.entries) {
  const item = { ...registry.defaults, ...entry };
  if (item.status !== 'public' || !item.sourceFile?.endsWith('.html') || !item.url?.startsWith('/') || item.url.includes('#')) continue;
  const group = item.territory || item.type || 'other';
  if (!groups.has(group)) groups.set(group, []);
  groups.get(group).push(item);
}
const sample = [...groups.values()].flatMap(items => items.sort((a,b) => a.url.localeCompare(b.url)).slice(0, 3)).slice(0, 45);
assert.ok(sample.length >= 12, 'Muestra insuficiente del registro');
const browser = await chromium.launch({headless:true});
const errors = [];
try {
  const context = await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});
  await context.route('**/*', route => route.request().url().startsWith(ROOT + '/') ? route.continue() : route.abort());
  const page = await context.newPage();
  for (const item of sample) {
    try {
      const response = await page.goto(ROOT + item.url, {waitUntil:'domcontentloaded'});
      assert.equal(response?.status(), 200);
      const result = await page.evaluate(() => ({title:document.querySelector('h1')?.textContent?.trim(),canonical:document.querySelector('link[rel=canonical]')?.href,body:document.querySelector('main')?.innerText?.trim().length || 0,links:[...document.querySelectorAll('main a[href^="/"]')].filter(a=>a.getClientRects().length && getComputedStyle(a).visibility !== 'hidden').length}));
      assert.ok(result.title, 'Sin H1');
      assert.ok(result.canonical?.startsWith('https://davidportodiaz.com/'), 'Canonical ausente');
      assert.ok(result.body > 100, 'Contenido insuficiente');
      assert.ok(result.links > 0, 'Sin enlaces internos visibles en main');
    } catch (error) { errors.push(item.url + ': ' + error.message); }
  }
  await context.close();
} finally { await browser.close(); }
assert.deepEqual(errors, [], errors.join('\n'));
console.log('PASS nojs registry content links: ' + sample.length);