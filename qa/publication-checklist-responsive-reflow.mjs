import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=(process.env.QA_ORIGIN||process.env.SITE_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});

try {
  for(const width of [320,768,1024,1440]){
    const page=await browser.newPage({viewport:{width,height:900}});
    const response=await page.goto(BASE+'/publicar-web/',{waitUntil:'load'});
    assert(response?.ok(),`/publicar-web/ ${width}px: HTTP ${response?.status()}`);
    const data=await page.evaluate(()=>{
      const nodes=[...document.querySelectorAll('main h1,main li,main li a')];
      return {
        viewport:document.documentElement.clientWidth,
        scroll:document.documentElement.scrollWidth,
        nodes:nodes.map(node=>{
          const r=node.getBoundingClientRect();
          return {text:node.textContent.trim().slice(0,90),left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width};
        })
      };
    });
    assert(data.nodes.length>=6,`/publicar-web/ ${width}px: faltan instrucciones visibles`);
    assert(data.scroll<=data.viewport+2,`/publicar-web/ ${width}px: desplazamiento horizontal ${data.scroll-data.viewport}px`);
    for(const node of data.nodes){
      assert(node.left>=-1&&node.right<=width+1,`/publicar-web/ ${width}px: elemento fuera del viewport: ${JSON.stringify(node)}`);
      assert(node.width>0&&node.bottom>node.top,`/publicar-web/ ${width}px: elemento sin geometría legible: ${JSON.stringify(node)}`);
    }
    await page.close();
  }
}finally{await browser.close();}
console.log('PASS publication-checklist-responsive-reflow');