import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import {resolve,extname,sep} from 'node:path';
import {chromium} from 'playwright';

const ROOT=process.cwd();
const ORIGIN='http://127.0.0.1:4173';
const TYPES={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.webp':'image/webp','.png':'image/png','.woff2':'font/woff2','.svg':'image/svg+xml'};
const browser=await chromium.launch({headless:true});
try{
  const context=await browser.newContext({serviceWorkers:'block',viewport:{width:1280,height:900},reducedMotion:'reduce'});
  await context.addInitScript(()=>localStorage.setItem('nl-popup-ts',String(Date.now())));
  const page=await context.newPage();
  await page.route('**/*',async route=>{
    const u=new URL(route.request().url());
    if(u.origin!==ORIGIN)return route.abort();
    if(u.pathname==='/assets/reading-market.json')return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({schema_version:1,offers:[],ratings:[]})});
    const rel=u.pathname.endsWith('/')?u.pathname.slice(1)+'index.html':u.pathname.slice(1);
    const file=resolve(ROOT,rel||'index.html');
    if(!file.startsWith(ROOT+sep)||!existsSync(file))return route.fulfill({status:404,body:'Not found'});
    return route.fulfill({status:200,contentType:TYPES[extname(file)]||'application/octet-stream',body:readFileSync(file)});
  });
  await page.goto(ORIGIN+'/recomendaciones/',{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>document.querySelector('[data-filter="orden"]')?.disabled===false);
  const total=await page.locator('[data-catalogue-book]').count();
  assert.ok(total>48);
  await page.locator('[data-filter="orden"]').selectOption('precio_asc');
  const prices=await page.locator('.catalogue-grid [data-catalogue-book]').evaluateAll(cards=>cards.filter(c=>!c.hidden).map(c=>Number(c.dataset.pvp)));
  assert.equal(prices.length,24);
  assert(prices.every(n=>Number.isFinite(n)&&n>0));
  assert(prices.every((value,i)=>i===0||value>=prices[i-1]),'Las tarjetas no siguen el PVP ascendente');
  const next=page.locator('.catalogue-pagination').getByRole('button',{name:'Siguiente →'});
  assert.equal(await next.isEnabled(),true);
  await next.focus();
  await page.keyboard.press('Enter');
  const hash=new URLSearchParams(new URL(page.url()).hash.slice(1));
  assert.equal(hash.get('pagina'),'2');
  assert.equal(await page.evaluate(()=>document.activeElement?.matches('.catalogue-results-head h2')),true,'Foco perdido tras paginar');
  assert.match(await page.locator('[data-catalogue-count]').innerText(),/página 2/);
  const second=await page.locator('.catalogue-grid [data-catalogue-book]').evaluateAll(cards=>cards.filter(c=>!c.hidden).map(c=>Number(c.dataset.pvp)));
  assert(second.every(n=>Number.isFinite(n)&&n>=prices.at(-1)),'La página 2 rompe el orden global');
  await context.close();
}finally{await browser.close();}
console.log('PASS PVP ordering and keyboard pagination focus');