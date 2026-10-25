import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const BASE=process.env.RECOMMENDATIONS_BASE_URL||'http://127.0.0.1:4173';
const browser=await chromium.launch();
try{
 const context=await browser.newContext({javaScriptEnabled:false});
 await context.route(/^https?:\/\//,r=>new URL(r.request().url()).origin===new URL(BASE).origin?r.continue():r.abort());
 const page=await context.newPage();
 await page.goto(BASE+'/recomendaciones/');
 const links=await page.locator('[data-catalogue-book] h3 a[href]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('href')));
 assert.ok(links.length>0);
 for(const href of new Set(links)){
  assert.match(href,/^\/recomendaciones\/libros\/[a-z0-9-]+\/$/);
  const response=await page.goto(BASE+href,{waitUntil:'domcontentloaded'});
  assert.equal(response.status(),200,href);
  assert.equal(await page.locator('main h1').count(),1,href);
 }
 console.log(`PASS ${links.length} book links`);
}finally{await browser.close();}