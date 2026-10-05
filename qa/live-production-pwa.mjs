import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';

const ORIGIN=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const swSource=fs.readFileSync('service-worker.js','utf8');
const version=swSource.match(/const CACHE_VERSION = `\$\{CACHE_NAMESPACE\}-(v\d+)`;/)?.[1];
assert.ok(version,'Cannot derive current PWA cache version');
const STATIC=`david-porto-pwa-${version}-static`;
const PAGES=`david-porto-pwa-${version}-pages`;
const appShellMatch=swSource.match(/const APP_SHELL = \[([\s\S]*?)\];/);
assert.ok(appShellMatch,'APP_SHELL missing');
const APP_SHELL=[...appShellMatch[1].matchAll(/["']([^"']+)["']/g)].map(m=>m[1]);

const browser=await chromium.launch({headless:true});
const context=await browser.newContext({
  viewport:{width:390,height:844},
  serviceWorkers:'allow',
  reducedMotion:'reduce',
});
const page=await context.newPage();
const pageErrors=[];
const externalAfterOffline=[];
page.on('pageerror',e=>pageErrors.push(String(e)));
await page.route(/(?:gc\.zgo\.at|goatcounter\.com|metricool\.com|clarity\.ms|c\.bing\.com)/,route=>route.abort());

try{
  const initial=await page.goto(`${ORIGIN}/?qa_live_pwa=1`,{waitUntil:'load',timeout:30000});
  assert.equal(initial?.status(),200,'home navigation failed');

  const registration=await page.evaluate(async()=>{
    const deadline=Date.now()+15000;
    while(Date.now()<deadline){
      const reg=await navigator.serviceWorker.getRegistration('/');
      if(reg?.active){
        await navigator.serviceWorker.ready;
        return {scope:reg.scope,state:reg.active.state,controlled:Boolean(navigator.serviceWorker.controller)};
      }
      await new Promise(r=>setTimeout(r,200));
    }
    return null;
  });
  assert.ok(registration,'production service worker did not register');
  assert.equal(registration.scope,ORIGIN+'/', 'unexpected service worker scope');
  assert.equal(registration.state,'activated','service worker not activated');

  if(!registration.controlled){
    const reloaded=await page.reload({waitUntil:'load',timeout:30000});
    assert.equal(reloaded?.status(),200,'controlled reload failed');
    await page.waitForFunction(()=>Boolean(navigator.serviceWorker.controller),null,{timeout:10000});
  }

  const swState=await page.evaluate(async({staticName,pageName,shell})=>{
    const keys=await caches.keys();
    const current=await navigator.serviceWorker.getRegistration('/');
    const cached={};
    for(const url of shell) cached[url]=Boolean(await caches.match(url));
    return {
      keys,
      controlled:Boolean(navigator.serviceWorker.controller),
      state:current?.active?.state||null,
      cached,
      staticPresent:keys.includes(staticName),
      pagesPresent:keys.includes(pageName),
    };
  },{staticName:STATIC,pageName:PAGES,shell:APP_SHELL});

  assert.equal(swState.controlled,true,'page is not controlled by deployed service worker');
  assert.equal(swState.state,'activated','deployed service worker lost activated state');
  assert.equal(swState.staticPresent,true,`current static cache missing: ${STATIC}`);
  for(const [url,ok] of Object.entries(swState.cached)) assert.equal(ok,true,`APP_SHELL entry not cached in production: ${url}`);
  const staleNamespaced=swState.keys.filter(k=>k.startsWith('david-porto-pwa-')&&!new Set([STATIC,PAGES]).has(k));
  assert.deepEqual(staleNamespaced,[],`fresh profile contains obsolete namespaced PWA cache(s): ${staleNamespaced.join(', ')}`);

  // Use an existing route that has not been visited in this fresh profile.
  // With network disabled it cannot be in PAGE_CACHE, so a controlled
  // navigation must fall back to cached /offline.html while preserving URL.
  const target=`${ORIGIN}/metodologia-editorial/?qa_live_pwa_offline=1`;
  let offlineRequests=false;
  const listener=req=>{
    try{
      const u=new URL(req.url());
      if(u.origin!==ORIGIN) externalAfterOffline.push(req.url());
    }catch{}
  };
  context.on('request',listener);
  await context.setOffline(true);
  offlineRequests=true;
  assert.equal(await page.evaluate(()=>navigator.onLine),false,'navigator.onLine did not become false');
  const offlineResponse=await page.goto(target,{waitUntil:'domcontentloaded',timeout:15000});
  assert.ok(offlineResponse,'offline navigation returned no response');
  assert.equal(offlineResponse.fromServiceWorker(),true,'offline fallback was not served by service worker');
  assert.equal(page.url(),target,'offline fallback changed requested URL');
  assert.equal(await page.locator('#offline-title').isVisible().catch(()=>false),true,'deployed offline fallback not rendered');
  assert.equal(externalAfterOffline.length,0,`offline fallback attempted third-party requests: ${externalAfterOffline.join(', ')}`);

  await context.setOffline(false);
  assert.equal(await page.evaluate(()=>navigator.onLine),true,'navigator.onLine did not recover');
  const recovered=await page.reload({waitUntil:'domcontentloaded',timeout:30000});
  assert.equal(recovered?.status(),200,'online recovery did not return target page');
  assert.equal(await page.locator('#offline-title').count(),0,'offline fallback remained after network recovery');
  assert.match((await page.locator('h1').first().innerText()).trim(),/metodolog/i,'recovered route did not render expected page');

  const finalState=await page.evaluate(async()=>({
    controlled:Boolean(navigator.serviceWorker.controller),
    caches:await caches.keys(),
  }));
  assert.equal(finalState.controlled,true,'service worker lost control after recovery');
  assert.deepEqual(pageErrors,[],`page errors: ${pageErrors.join(' | ')}`);
  console.log('PASS live production PWA:',JSON.stringify({
    version,
    appShellEntries:APP_SHELL.length,
    caches:finalState.caches,
    offlineFallback:true,
    sameUrlRecovery:true,
  }));
}finally{
  await context.close();
  await browser.close();
}
