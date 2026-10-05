import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';
import { assertProductionRelease } from './production-release-marker.mjs';

const O=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const S=(process.env.EXPECTED_RELEASE_SHA||'').trim();
const sw=fs.readFileSync('service-worker.js','utf8');
const version=sw.match(/const CACHE_VERSION = `\$\{CACHE_NAMESPACE\}-(v\d+)`;/)?.[1];
assert.ok(version,'PWA network-first refresh: cache version missing');
const PAGE_CACHE=`david-porto-pwa-${version}-pages`;
const ROUTE='/convocatorias-escritores/';
const SENTINEL='__QA_STALE_PAGE_SENTINEL__';

await assertProductionRelease({origin:O,sha:S,label:'pwa-network-first-refresh'});

const browser=await chromium.launch({headless:true});
try{
  const context=await browser.newContext({
    viewport:{width:390,height:844},
    isMobile:true,
    hasTouch:true,
    serviceWorkers:'allow',
    reducedMotion:'reduce',
  });
  const page=await context.newPage();
  const errors=[];
  page.on('pageerror',e=>errors.push(String(e)));

  const bootstrap=await page.goto(O+'/?qa_pwa_refresh=bootstrap',{waitUntil:'domcontentloaded',timeout:25000});
  assert.equal(bootstrap?.status(),200,'PWA network-first bootstrap failed');
  await page.evaluate(async()=>{
    const reg=await navigator.serviceWorker.register('/service-worker.js');
    await navigator.serviceWorker.ready;
    const worker=reg.active||reg.waiting||reg.installing;
    if(worker&&worker.state!=='activated'){
      await new Promise(resolve=>{
        const timer=setTimeout(resolve,8000);
        worker.addEventListener('statechange',function onChange(){
          if(worker.state!=='activated')return;
          clearTimeout(timer);
          worker.removeEventListener('statechange',onChange);
          resolve();
        });
      });
    }
  });
  await page.reload({waitUntil:'domcontentloaded',timeout:25000});
  assert.equal(await page.evaluate(()=>Boolean(navigator.serviceWorker.controller)),true,'page not controlled by service worker');

  const url=`${O}${ROUTE}?qa_pwa_network_first=${encodeURIComponent(S||'live')}`;
  await page.evaluate(async({cacheName,url,sentinel})=>{
    const cache=await caches.open(cacheName);
    await cache.put(url,new Response(
      `<!doctype html><html lang="es"><head><title>${sentinel}</title></head><body><main><h1>${sentinel}</h1></main></body></html>`,
      {status:200,headers:{'content-type':'text/html; charset=utf-8'}},
    ));
  },{cacheName:PAGE_CACHE,url,sentinel:SENTINEL});

  const seeded=await page.evaluate(async({url,sentinel})=>{
    const r=await caches.match(url);
    return r ? (await r.text()).includes(sentinel) : false;
  },{url,sentinel:SENTINEL});
  assert.equal(seeded,true,'failed to seed deliberately stale cached HTML');

  const response=await page.goto(url,{waitUntil:'domcontentloaded',timeout:25000});
  assert.equal(response?.status(),200,'online navigation failed');
  const liveH1=(await page.locator('h1').first().textContent()||'').trim();
  assert.ok(liveH1,'live response missing H1');
  assert.notEqual(liveH1,SENTINEL,'online navigation served stale PAGE_CACHE instead of network');

  await page.waitForTimeout(150);
  const refreshed=await page.evaluate(async({url,sentinel})=>{
    const r=await caches.match(url);
    if(!r)return {hit:false,stale:null,body:''};
    const body=await r.text();
    return {hit:true,stale:body.includes(sentinel),body};
  },{url,sentinel:SENTINEL});
  assert.equal(refreshed.hit,true,'online navigation did not retain refreshed page in cache');
  assert.equal(refreshed.stale,false,'stale cache entry was not replaced after successful online navigation');
  assert.ok(refreshed.body.includes('<h1'),'refreshed cached HTML missing H1');

  await context.setOffline(true);
  const offline=await page.goto(url,{waitUntil:'domcontentloaded',timeout:10000});
  assert.equal(offline?.status(),200,'refreshed cached page unavailable offline');
  assert.notEqual((await page.locator('h1').first().textContent()||'').trim(),SENTINEL,'offline fallback regressed to stale sentinel');
  await context.setOffline(false);

  assert.deepEqual(errors,[],'PWA network-first page errors: '+errors.join(' | '));
  await context.close();
}finally{
  await browser.close();
}

console.log(`PASS PWA network-first refresh: stale ${ROUTE} cache is replaced online and reused offline`);
