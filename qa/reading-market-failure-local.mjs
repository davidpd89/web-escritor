import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import {resolve,extname,sep} from 'node:path';
import {chromium} from 'playwright';

const ROOT=process.cwd();
const ORIGIN='http://127.0.0.1:4173';
const TYPES={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.webp':'image/webp','.png':'image/png','.woff2':'font/woff2','.svg':'image/svg+xml'};
const browser=await chromium.launch({headless:true});
try{
  const context=await browser.newContext({serviceWorkers:'block',viewport:{width:390,height:844},reducedMotion:'reduce'});
  await context.addInitScript(()=>localStorage.setItem('nl-popup-ts',String(Date.now())));
  const page=await context.newPage();
  let marketRequests=0;
  await page.route('**/*',async route=>{
    const u=new URL(route.request().url());
    if(u.origin!==ORIGIN)return route.abort();
    if(u.pathname==='/assets/reading-market.json'){marketRequests++;return route.abort('failed');}
    const rel=u.pathname.endsWith('/')?u.pathname.slice(1)+'index.html':u.pathname.slice(1);
    const file=resolve(ROOT,rel||'index.html');
    if(!file.startsWith(ROOT+sep)||!existsSync(file))return route.fulfill({status:404,body:'Not found'});
    return route.fulfill({status:200,body:readFileSync(file),contentType:TYPES[extname(file)]||'application/octet-stream'});
  });
  const response=await page.goto(ORIGIN+'/recomendaciones/',{waitUntil:'domcontentloaded'});
  assert.equal(response.status(),200);
  await page.waitForFunction(()=>document.querySelector('[data-catalogue-filters] fieldset')?.disabled===false);
  assert.ok(marketRequests>=1,'No se simuló el fallo del recurso de mercado');
  const total=await page.locator('[data-catalogue-book]').count();
  assert.ok(total>50);
  await page.locator('[data-filter="q"]').fill('Coraline');
  const selected=await page.locator('[data-catalogue-book]:not([hidden])').count();
  assert.ok(selected>=1&&selected<total,'La búsqueda dejó de funcionar');
  const titles=await page.locator('[data-catalogue-book]:not([hidden])').evaluateAll(es=>es.map(e=>e.dataset.title));
  assert(titles.every(title=>title.toLowerCase().includes('coraline')));
  const buy=page.locator('[data-catalogue-book]:not([hidden]) .catalogue-card__buy').first();
  assert.match(await buy.getAttribute('href'),/^https:\/\/www\.amazon\.es\//);
  assert.equal(await buy.getAttribute('target'),'_blank');
  await page.locator('[data-catalogue-filters] [type="reset"]').click();
  await page.waitForFunction(()=>document.querySelector('[data-filter="q"]').value==='');
  assert.equal(await page.locator('[data-catalogue-book]:not([hidden])').count(),Math.min(total,24));
  await context.close();
}finally{await browser.close();}
console.log('PASS static catalogue survives market JSON failure');