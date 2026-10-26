import test from 'node:test';
import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = process.env.SITE_URL || process.env.BASE_URL || 'http://127.0.0.1:8000';
const route = '/accesibilidad/';

test('identidad estructurada y metadatos del documento servido', async () => {
  const browser = await chromium.launch({headless:true});
  try {
    for (const javaScriptEnabled of [true,false]) {
      const context = await browser.newContext({javaScriptEnabled});
      try {
        const page = await context.newPage();
        const response = await page.goto(new URL(route,base).href,{waitUntil:'domcontentloaded'});
        assert.equal(response?.status(),200,`${route}: HTTP`);
        const data = await page.evaluate(()=>({
          canonical:document.querySelector('link[rel="canonical"]')?.href,
          ogUrl:document.querySelector('meta[property="og:url"]')?.content,
          ogTitle:document.querySelector('meta[property="og:title"]')?.content,
          title:document.title,
          schemas:[...document.querySelectorAll('script[type="application/ld+json"]')].map(s=>s.textContent)
        }));
        const label=`${route} JS=${javaScriptEnabled}`;
        assert.ok(data.canonical,`${label}: falta canonical`);
        assert.equal(data.ogUrl,data.canonical,`${label}: og:url ${data.ogUrl}`);
        assert.match(data.title,/accesibilidad/i,`${label}: title ${data.title}`);
        assert.match(data.ogTitle||'',/accesibilidad/i,`${label}: og:title ${data.ogTitle}`);
        const nodes=[];
        for (const source of data.schemas) {
          let parsed;
          assert.doesNotThrow(()=>{parsed=JSON.parse(source);},`${label}: JSON-LD inválido`);
          const visit=obj=>{
            if (!obj || typeof obj!=='object') return;
            if (Array.isArray(obj)) return obj.forEach(visit);
            if (obj['@type']==='WebPage' || (Array.isArray(obj['@type']) && obj['@type'].includes('WebPage'))) nodes.push(obj);
            if (obj['@graph']) visit(obj['@graph']);
          };
          visit(parsed);
        }
        assert.equal(nodes.length,1,`${label}: WebPage encontrados ${nodes.length}`);
        assert.equal(nodes[0].url,data.canonical,`${label}: WebPage.url ${nodes[0].url}`);
        assert.equal(nodes[0]['@id'],data.canonical+'#page',`${label}: WebPage.@id ${nodes[0]['@id']}`);
      } finally { await context.close(); }
    }
  } finally { await browser.close(); }
});