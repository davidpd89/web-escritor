import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const O=(process.env.QA_ORIGIN||'http://127.0.0.1:4173').replace(/\/$/,'');
const routes=['/','/libros/','/cuaderno/','/recomendaciones/','/editoriales/','/convocatorias-escritores/','/herramientas/','/asistente/','/eventos.html','/ferias.html','/privacidad.html'];
const browser=await chromium.launch({headless:true});
const failures=[];
try{
  for(const width of [320,390,768]){
    const context=await browser.newContext({javaScriptEnabled:false,viewport:{width,height:850}});
    await context.route('**/*',r=>{if(/\.(?:woff2?|ttf|otf)(?:\?|$)/i.test(r.request().url()))return r.abort();return r.request().url().startsWith(O+'/')?r.continue():r.abort();});
    const page=await context.newPage();
    for(const route of routes){
      await page.goto(O+route,{waitUntil:'load'});
      const s=await page.evaluate(()=>{const h=document.querySelector('h1');const r=h?.getBoundingClientRect();return {overflow:Math.max(document.documentElement.scrollWidth,document.body.scrollWidth)-innerWidth,h1:h?.innerText.trim(),visible:!!r&&r.width>0&&r.height>0,main:document.querySelector('main')?.innerText.trim().length||0};});
      if(!s.visible||!s.h1||s.main<100||s.overflow>1)failures.push(route+' @'+width+': '+JSON.stringify(s));
    }
    await context.close();
  }
}finally{await browser.close();}
assert.deepEqual(failures,[],failures.join('\n'));
console.log('PASS nojs font failure responsive matrix');