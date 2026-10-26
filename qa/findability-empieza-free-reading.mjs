import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const O=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true});
try {
  const context=await browser.newContext({viewport:{width:390,height:900},serviceWorkers:'block'});
  await context.route('**/*',r=>r.request().url().startsWith(O+'/')?r.continue():r.abort());
  const page=await context.newPage();
  await page.goto(O+'/empieza-aqui/');
  await page.locator('main a[href="/fragmento/"]').click();
  assert.equal(new URL(page.url()).pathname,'/fragmento/');
  assert.match(await page.title(),/Samuel entre mundos/i);
  const article=page.locator('main article.fragment-reading.fragment-text');
  assert(await article.isVisible(),'El capítulo no es visible');
  const text=await article.innerText();
  assert(text.length>2000,`El capítulo ofrece solo ${text.length} caracteres`);
  assert(/El principio del salto/i.test(text),'No se identifica el capítulo');
  const paragraphs=article.locator('p:visible');
  assert(await paragraphs.count()>=8,'El contenido de lectura resulta insuficiente');
  const blocked=await page.evaluate(()=>{
    const main=document.querySelector('main');
    return !main||main.closest('[inert],[aria-hidden="true"]')!==null;
  });
  assert(!blocked,'El contenido está oculto a tecnologías asistivas');
  await context.close();
} finally {await browser.close();}
console.log('EMPIEZA FREE READING: OK');