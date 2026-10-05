import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';
import { assertProductionRelease } from './production-release-marker.mjs';

const O=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const S=(process.env.EXPECTED_RELEASE_SHA||'').trim();
const sw=fs.readFileSync('service-worker.js','utf8');
const version=sw.match(/const CACHE_VERSION = `\$\{CACHE_NAMESPACE\}-(v\d+)`;/)?.[1];
assert.ok(version,'production PWA page-cache: cache version missing');
const PAGE_CACHE=`david-porto-pwa-${version}-pages`;
const ROUTES=[
  '/las-manecillas-del-recuerdo/',
  '/cuaderno/que-es-el-portal-fantasy/',
  '/editoriales/',
  '/convocatorias-escritores/',
  '/metodologia-editorial/',
];

await assertProductionRelease({origin:O,sha:S,label:'pwa-page-cache'});

const browser=await chromium.launch({headless:true});
try{
  const context=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:'allow',reducedMotion:'reduce'});
  const page=await context.newPage();
  const errors=[];
  page.on('pageerror',e=>errors.push(String(e)));

  const home=await page.goto(`${O}/?qa_pwa_page_cache=bootstrap`,{waitUntil:'domcontentloaded',timeout:25000});
  assert.equal(home?.status(),200,'PWA page-cache bootstrap failed');
  await page.evaluate(async()=>{
    const reg=await navigator.serviceWorker.register('/service-worker.js');
    await navigator.serviceWorker.ready;
    const worker=reg.active||reg.waiting||reg.installing;
    if(worker&&worker.state!=='activated'){
      await new Promise(resolve=>{
        const timer=setTimeout(resolve,8000);
        worker.addEventListener('statechange',function onChange(){
          if(worker.state!=='activated') return;
          worker.removeEventListener('statechange',onChange);
          clearTimeout(timer);
          resolve();
        });
      });
    }
  });
  await page.reload({waitUntil:'domcontentloaded',timeout:25000});
  assert.equal(await page.evaluate(()=>Boolean(navigator.serviceWorker.controller)),true,'PWA page-cache page not controlled');

  const cached=[];
  for(const route of ROUTES){
    const url=`${O}${route}?qa_pwa_page_cache=${encodeURIComponent(S||'live')}`;
    const r=await page.goto(url,{waitUntil:'domcontentloaded',timeout:25000});
    assert.equal(r?.status(),200,`${route}: HTTP ${r?.status()}`);
    const h1=(await page.locator('h1').first().textContent()||'').trim();
    assert.ok(h1,`${route}: missing H1 before cache verification`);
    await page.waitForTimeout(100);

    const entry=await page.evaluate(async url=>{
      const keys=await caches.keys();
      const response=await caches.match(url);
      return {
        keys,
        hit:Boolean(response),
        status:response?.status||null,
        type:response?.headers.get('content-type')||'',
        body:response?await response.text():'',
      };
    },url);
    assert.ok(entry.keys.includes(PAGE_CACHE),`${route}: expected page cache ${PAGE_CACHE} missing: ${entry.keys.join(', ')}`);
    assert.equal(entry.hit,true,`${route}: visited production page was not cached`);
    assert.equal(entry.status,200,`${route}: cached status ${entry.status}`);
    assert.match(entry.type,/text\/html/i,`${route}: cached response is not HTML: ${entry.type}`);
    assert.ok(entry.body.includes('<h1'),`${route}: cached HTML missing H1 markup`);
    cached.push({route,url,h1});
  }

  const missing=`${O}/__qa-pwa-cache-missing__?qa=${encodeURIComponent(S||'live')}`;
  const notFound=await page.goto(missing,{waitUntil:'domcontentloaded',timeout:25000});
  assert.equal(notFound?.status(),404,'PWA page-cache missing route must stay 404');
  assert.equal(await page.evaluate(async url=>Boolean(await caches.match(url)),missing),false,'PWA page-cache cached a 404 response');

  await context.setOffline(true);
  const offlineHits=await page.evaluate(async urls=>Object.fromEntries(await Promise.all(urls.map(async u=>[u,Boolean(await caches.match(u))]))),cached.map(x=>x.url));
  assert.ok(Object.values(offlineHits).every(Boolean),`cached pages unavailable from CacheStorage while offline: ${JSON.stringify(offlineHits)}`);
  await context.setOffline(false);

  assert.deepEqual(errors,[],`PWA page-cache page errors: ${errors.join(' | ')}`);
  console.log('PASS production PWA page cache:',JSON.stringify({cache:PAGE_CACHE,routes:cached.map(x=>x.route),offlineHits}));
  await context.close();
}finally{
  await browser.close();
}
