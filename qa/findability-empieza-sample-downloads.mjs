import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const O=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true});
try {
  const context=await browser.newContext({serviceWorkers:'block'});
  await context.route('**/*',r=>r.request().url().startsWith(O+'/')?r.continue():r.abort());
  const page=await context.newPage();
  await page.goto(O+'/empieza-aqui/');
  await page.locator('main a[href="/las-manecillas-del-recuerdo/kindle/#muestra"]').click();
  assert.equal(new URL(page.url()).hash,'#muestra');
  for(const ext of ['epub','txt']) {
    const link=page.locator(`section:has(#formatos-title) [data-sample-download="${ext}"]`);
    assert.equal(await link.count(),1,`Falta descarga ${ext}`);
    assert(await link.isVisible(),`Descarga ${ext} oculta`);
    assert(await link.getAttribute('download')!==null,`${ext}: falta atributo download`);
    const href=await link.getAttribute('href');
    assert(href.startsWith('/assets/downloads/'),`${ext}: URL no local`);
    const response=await context.request.get(O+href);
    assert.equal(response.status(),200,`${ext}: recurso inaccesible`);
    const bytes=await response.body();
    assert(bytes.length>1024,`${ext}: archivo demasiado pequeño`);
    if(ext==='epub') assert.equal(bytes.subarray(0,2).toString('ascii'),'PK','EPUB sin cabecera ZIP');
    else assert.doesNotThrow(()=>new TextDecoder('utf-8',{fatal:true}).decode(bytes),'TXT inválido');
  }
  await context.close();
} finally {await browser.close();}
console.log('EMPIEZA SAMPLE DOWNLOADS: OK');