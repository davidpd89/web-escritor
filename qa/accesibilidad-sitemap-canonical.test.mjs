import test from 'node:test';
import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = process.env.SITE_URL || process.env.BASE_URL || 'http://127.0.0.1:8000';
const route = '/accesibilidad/';
const expected = 'https://davidportodiaz.com/accesibilidad/';

test('sitemap y canonical publicada representan una única identidad', async () => {
  const browser = await chromium.launch({headless:true});
  try {
    const page = await browser.newPage();
    const response = await page.goto(new URL(route,base).href,{waitUntil:'domcontentloaded'});
    assert.equal(response?.status(),200,`${route}: respuesta HTTP`);
    const canonical = await page.locator('link[rel="canonical"]').getAttribute('href');
    assert.equal(canonical,expected,`${route}: canonical ${canonical}`);
    const sitemapResponse = await page.request.get(new URL('/sitemap.xml',base).href);
    assert.equal(sitemapResponse.status(),200,'/sitemap.xml: respuesta HTTP');
    const xml = await sitemapResponse.text();
    const locs = [...xml.matchAll(/<loc>\s*([^<]+)\s*<\/loc>/g)].map(m=>m[1].trim());
    assert.equal(locs.filter(url=>url===canonical).length,1,`${route}: apariciones de ${canonical} en sitemap`);
    const alternatives = locs.filter(url=>{
      try { const u=new URL(url); return u.hostname==='davidportodiaz.com' && u.pathname.replace(/\/$/,'')==='/accesibilidad' && url!==canonical; }
      catch { return false; }
    });
    assert.deepEqual(alternatives,[],`${route}: identidades alternativas ${alternatives.join(', ')}`);
  } finally { await browser.close(); }
});