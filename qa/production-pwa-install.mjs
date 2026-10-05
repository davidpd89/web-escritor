import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';
import { assertProductionRelease } from './production-release-marker.mjs';

const O=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const S=(process.env.EXPECTED_RELEASE_SHA||'').trim();
const sw=fs.readFileSync('service-worker.js','utf8');
const version=sw.match(/const CACHE_VERSION = `\$\{CACHE_NAMESPACE\}-(v\d+)`;/)?.[1];
const shellMatch=sw.match(/const APP_SHELL = \[([\s\S]*?)\];/);
assert.ok(version,'PWA production audit: cache version missing');
assert.ok(shellMatch,'PWA production audit: APP_SHELL missing');
const appShell=[...shellMatch[1].matchAll(/["']([^"']+)["']/g)].map(x=>x[1]);
const expectedCaches=[`david-porto-pwa-${version}-static`,`david-porto-pwa-${version}-pages`];

await assertProductionRelease({origin:O,sha:S,label:'pwa-install'});

const browser=await chromium.launch({headless:true});
try{
  const context=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:'allow'});
  const page=await context.newPage();
  const errors=[];
  page.on('pageerror',e=>errors.push(String(e)));
  const r=await page.goto(`${O}/?qa_pwa_install=${encodeURIComponent(S||'live')}`,{waitUntil:'domcontentloaded',timeout:25000});
  assert.equal(r?.status(),200,'PWA production home navigation failed');

  const registration=await page.evaluate(async()=>{
    const reg=await navigator.serviceWorker.register('/service-worker.js');
    await navigator.serviceWorker.ready;
    const active=reg.active||reg.waiting||reg.installing;
    if(active&&active.state!=='activated') await new Promise(resolve=>{
      const timer=setTimeout(resolve,8000);
      active.addEventListener('statechange',function listener(){if(active.state==='activated'){clearTimeout(timer);active.removeEventListener('statechange',listener);resolve()} });
    });
    if(!navigator.serviceWorker.controller){
      await new Promise(resolve=>{const timer=setTimeout(resolve,5000);navigator.serviceWorker.addEventListener('controllerchange',()=>{clearTimeout(timer);resolve()},{once:true})});
      if(!navigator.serviceWorker.controller) location.reload();
    }
    return {scope:reg.scope,state:reg.active?.state||null,scriptURL:reg.active?.scriptURL||null};
  });
  assert.equal(registration.scope,`${O}/`,'PWA production scope drift');
  assert.equal(registration.state,'activated','PWA production worker not activated');
  assert.equal(new URL(registration.scriptURL).pathname,'/service-worker.js','PWA production script URL drift');

  const cacheState=await page.evaluate(async shell=>({
    keys:await caches.keys(),
    shell:Object.fromEntries(await Promise.all(shell.map(async path=>[path,Boolean(await caches.match(path))]))),
  }),appShell);
  for(const name of expectedCaches) assert.ok(cacheState.keys.includes(name),`PWA production missing cache ${name}: ${cacheState.keys.join(', ')}`);
  for(const [path,present] of Object.entries(cacheState.shell)) assert.equal(present,true,`PWA production APP_SHELL not precached: ${path}`);

  const cdp=await context.newCDPSession(page);
  const manifest=await cdp.send('Page.getAppManifest');
  assert.equal(manifest.errors?.length||0,0,`PWA production manifest errors: ${JSON.stringify(manifest.errors)}`);
  try{
    const install=await cdp.send('Page.getInstallabilityErrors');
    const meaningful=(install.installabilityErrors||[]).filter(x=>x.errorId!=='in-incognito');
    assert.deepEqual(meaningful,[],`PWA production installability errors: ${JSON.stringify(meaningful)}`);
  }catch(e){
    if(!/method|not found|unknown command/i.test(String(e?.message||e))) throw e;
  }
  assert.deepEqual(errors,[],'PWA production page errors: '+errors.join(' | '));
  await context.close();
}finally{await browser.close()}

console.log(`PASS production PWA installability: ${version}, ${appShell.length} APP_SHELL entries`);
