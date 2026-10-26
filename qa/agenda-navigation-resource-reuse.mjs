import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
  const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});
  const page=await context.newPage();
  const resources=[];
  page.on('response',r=>{const u=new URL(r.url());if(u.origin===new URL(BASE).origin&&/\.(css|js)$/.test(u.pathname)) resources.push({url:u.pathname+u.search,status:r.status(),cache:r.headers()['cache-control']||''});});
  for(const route of ['/ferias.html','/eventos.html']) {
    const response=await page.goto(BASE+route,{waitUntil:'networkidle'});
    assert.ok(response?.ok(),`${route}: HTTP ${response?.status()}`);
  }
  const failed=resources.filter(r=>r.status>=400);
  assert.deepEqual(failed,[],'ferias.html -> eventos.html: recursos CSS/JS con errores HTTP');
  const counts=new Map();
  for(const r of resources) counts.set(r.url,(counts.get(r.url)||0)+1);
  const repeated=[...counts].filter(([,count])=>count>1);
  const excessive=repeated.filter(([url])=>resources.some(r=>r.url===url&&/max-age=(?:[1-9]\d*)|immutable/.test(r.cache)));
  assert.deepEqual(excessive,[],'ferias.html -> eventos.html: recursos cacheables descargados repetidamente');
  assert.ok(resources.length>0,'ferias.html -> eventos.html: no se observaron recursos CSS/JS; revisar captura de red');
  await context.close();
} finally {await browser.close();}
