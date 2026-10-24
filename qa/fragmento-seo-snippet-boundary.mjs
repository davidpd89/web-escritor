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
    const result=await page.evaluate(()=>{const story=document.querySelector('.fragment-reading');const excluded=[...document.querySelectorAll('[data-nosnippet]')];const inside=[...story.querySelectorAll('p')].every(p=>!!p.closest('[data-nosnippet]'));const outside=['.article-header','.fragment-cta-box','.article-related','.editorial-newsletter'].every(s=>{const e=document.querySelector(s);return !!e&&!e.closest('[data-nosnippet]');});return {sections:excluded.length,inside,outside,paragraphs:story.querySelectorAll('p').length,description:document.querySelector('meta[name=description]')?.content||'',robots:document.querySelector('meta[name=robots]')?.content||''};});
    assert.equal(result.sections,1);
    assert.ok(result.paragraphs>30);
    assert.ok(result.inside,'La ficción queda expuesta a snippets');
    assert.ok(result.outside,'La conversión queda excluida de snippets');
    assert.match(result.description,/capítulo|gratis/i);
    assert.match(result.robots,/index/);
    await ctx.close();
  }
} finally {await browser.close();}
console.log('fragmento-seo-snippet-boundary: OK');