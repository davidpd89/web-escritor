import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const BASE=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true});
try {
  for(const javascript of [true,false]) {
    const ctx=await browser.newContext({javaScriptEnabled:javascript});
    const page=await ctx.newPage();
    await page.route('**/*',r=>r.request().url().startsWith(BASE)?r.continue():r.abort());
    await page.goto(BASE+'/fragmento/');
    const result=await page.locator('main').evaluate(main=>{const outer=main.querySelector('article[aria-labelledby]');const inner=main.querySelector('article.fragment-reading');const name=e=>{const id=e?.getAttribute('aria-labelledby');return id?document.getElementById(id)?.textContent?.trim()||'':'';};return {outer:name(outer),inner:name(inner),heading:inner?.querySelector('h2')?.textContent?.trim(),nested:!!outer?.contains(inner)};});
    assert.ok(result.nested);
    assert.equal(result.outer,'El principio del salto');
    assert.match(result.heading||'',/Capítulo 1/);
    assert.equal(result.inner,result.heading,'El artículo literario anidado no tiene nombre accesible asociado');
    await ctx.close();
  }
} finally {await browser.close();}
console.log('fragmento-article-region-names: OK');