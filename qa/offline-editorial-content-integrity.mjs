import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=(process.env.QA_ORIGIN||process.env.SITE_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
  const page=await browser.newPage({viewport:{width:390,height:844}});
  const response=await page.goto(BASE+'/offline.html',{waitUntil:'load'});
  assert(response?.ok(),`/offline.html: HTTP ${response?.status()}`);
  const result=await page.evaluate(()=>({lang:document.documentElement.lang,title:document.querySelector('main h1')?.textContent.trim(),lead:document.querySelector('main .lead')?.textContent.trim(),status:document.querySelector('main [role="status"]')?.textContent.trim(),body:document.querySelector('main')?.innerText||'',links:[...document.querySelectorAll('main a[href]')].map(a=>({text:a.textContent.trim(),url:a.href}))}));
  assert(result.lang.toLowerCase().startsWith('es'),`/offline.html: idioma ${result.lang}`);
  for(const field of ['title','lead','status']){
    assert(result[field]?.length>=12,`/offline.html: ${field} ausente o insuficiente: ${result[field]}`);
  }
  assert(!/\b(?:lorem ipsum|TODO|FIXME|texto de prueba|pendiente de redactar)\b/i.test(result.body),`/offline.html: texto editorial provisional`);
  for(const link of result.links){
    const url=new URL(link.url);
    assert(url.protocol==='https:'||url.origin===new URL(BASE).origin,`/offline.html: ${link.text}: enlace inseguro ${link.url}`);
  }
} finally {await browser.close();}
console.log('PASS offline-editorial-content-integrity');