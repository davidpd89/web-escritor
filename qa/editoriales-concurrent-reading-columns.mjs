import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=process.env.QA_ORIGIN||process.env.QA_BASE_URL||'http://127.0.0.1:4173';
const routes=['/editoriales/minotauro/','/editoriales/nocturna-ediciones/','/editoriales/duermevela-ediciones/'];
const widths=[320,768,1024,1440];
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
const errors=[];
try {
  for(const width of widths){
    const context=await browser.newContext({viewport:{width,height:900}});
    try {
      await Promise.all(routes.map(async route=>{
        const page=await context.newPage();
        try {
          const response=await page.goto(BASE+route,{waitUntil:'load'});
          assert.equal(response?.status(),200,`${route} ${width}px: HTTP ${response?.status()}`);
          await page.locator('.editorial-fact').first().waitFor({state:'visible'});
          const data=await page.evaluate(()=>{
            const blocks=[...document.querySelectorAll('.editorial-fact,.tool-source-list')];
            return {overflow:document.documentElement.scrollWidth-document.documentElement.clientWidth,blocks:blocks.map((el,i)=>{const r=el.getBoundingClientRect();const p=el.parentElement.getBoundingClientRect();return {i,width:r.width,left:r.left,right:r.right,parentLeft:p.left,parentRight:p.right,visible:getComputedStyle(el).display!=='none'};})};
          });
          assert.ok(data.blocks.length>=2,`${route} ${width}px: faltan bloques factuales o fuentes`);
          assert.ok(data.overflow<=1,`${route} ${width}px: overflow ${data.overflow}px`);
          for(const b of data.blocks){
            assert.ok(b.visible && b.width>0,`${route} ${width}px: bloque ${b.i} oculto o vacío`);
            assert.ok(b.left>=-1 && b.right<=width+1,`${route} ${width}px: bloque ${b.i} fuera del viewport (${b.left},${b.right})`);
            assert.ok(b.left>=b.parentLeft-2 && b.right<=b.parentRight+2,`${route} ${width}px: bloque ${b.i} excede su contenedor`);
          }
        }catch(e){errors.push(e.message);}finally{await page.close();}
      }));
    }finally{await context.close();}
  }
  assert.deepEqual(errors,[],errors.join('\n'));
  console.log('PASS editoriales reading columns');
}finally{await browser.close();}
