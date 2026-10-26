import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE=(process.env.BASE_URL||process.env.QA_BASE_URL||'http://127.0.0.1:8000').replace(/\/$/,'');
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
  const page=await browser.newPage({viewport:{width:390,height:844}});
  const requests=[];
  const failures=[];
  page.on('request',r=>{if(r.resourceType()==='stylesheet')requests.push(r.url());});
  page.on('requestfailed',r=>{if(r.resourceType()==='stylesheet')failures.push(r.url());});
  const response=await page.goto(BASE+'/mapa-del-sitio/',{waitUntil:'load'});
  assert(response?.ok(),`/mapa-del-sitio/: HTTP ${response?.status()}`);
  await page.locator('.findability-directory').waitFor({state:'visible'});
  const resources=await page.evaluate(()=>performance.getEntriesByType('resource').filter(r=>r.initiatorType==='link'&&new URL(r.name).pathname.endsWith('.css')).map(r=>({url:r.name,bytes:r.transferSize||r.encodedBodySize||0})));
  assert(resources.length>0,'/mapa-del-sitio/: no se han medido hojas CSS');
  assert.deepEqual(failures,[],`/mapa-del-sitio/: CSS fallido: ${failures.join(', ')}`);
  const duplicates=requests.filter((url,i)=>requests.indexOf(url)!==i);
  assert.deepEqual(duplicates,[],`/mapa-del-sitio/: CSS solicitado varias veces: ${duplicates.join(', ')}`);
  const bytes=resources.reduce((sum,r)=>sum+r.bytes,0);
  assert(bytes<=300*1024,`/mapa-del-sitio/: CSS transferido ${bytes} bytes, presupuesto 307200 bytes; ${JSON.stringify(resources)}`);
  await page.close();
} finally {await browser.close();}
console.log('PASS: findability CSS transfer budget');