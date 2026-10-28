import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=(process.env.QA_ORIGIN||process.env.SITE_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});

try{
  for(const width of [320,768,1024,1440]){
    const page=await browser.newPage({viewport:{width,height:900}});
    const response=await page.goto(BASE+'/convocatorias-escritores/',{waitUntil:'load'});
    assert(response?.ok(),`/convocatorias-escritores/ ${width}px: HTTP ${response?.status()}`);
    await page.evaluate(()=>document.fonts.ready);
    const data=await page.evaluate(()=>{
      const main=document.querySelector('main');
      if(!main)throw Error('Falta main');
      const r=main.getBoundingClientRect();
      const headings=[...main.querySelectorAll('h1,h2,h3')].filter(el=>el.getClientRects().length).map(el=>{
        const b=el.getBoundingClientRect();
        return {text:el.textContent.trim().slice(0,80),left:b.left,right:b.right,width:b.width};
      });
      return {
        viewport:document.documentElement.clientWidth,
        scroll:document.documentElement.scrollWidth,
        main:{left:r.left,right:r.right,width:r.width},
        headings
      };
    });
    assert(data.scroll<=data.viewport+2,`/convocatorias-escritores/ ${width}px: desplazamiento horizontal ${data.scroll-data.viewport}px`);
    assert(data.main.width>0,`/convocatorias-escritores/ ${width}px: main sin anchura`);
    assert(data.main.left>=-1&&data.main.right<=width+1,`/convocatorias-escritores/ ${width}px: main fuera del viewport: ${JSON.stringify(data.main)}`);
    assert(data.headings.length>0,`/convocatorias-escritores/ ${width}px: ningún encabezado visible`);
    for(const h of data.headings){
      assert(h.width>0&&h.left>=-1&&h.right<=width+1,`/convocatorias-escritores/ ${width}px: encabezado desbordado: ${JSON.stringify(h)}`);
    }
    await page.close();
  }
}finally{await browser.close();}
console.log('PASS radar-responsive-document-reflow');