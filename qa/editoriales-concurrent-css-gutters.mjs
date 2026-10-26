import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=process.env.QA_ORIGIN||process.env.QA_BASE_URL||'http://127.0.0.1:4173';
const routes=['/editoriales/','/editoriales/minotauro/','/editoriales/nocturna-ediciones/','/editoriales/duermevela-ediciones/'];
const widths=[320,768,1024,1440];
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
const failures=[];
try {
  for(const width of widths){
    const context=await browser.newContext({viewport:{width,height:900}});
    try {
      await Promise.all(routes.map(async route=>{
        const page=await context.newPage();
        const failed=[];
        page.on('response',r=>{if(new URL(r.url()).origin===new URL(BASE).origin && r.url().split('?')[0].endsWith('.css') && !r.ok())failed.push(`${r.status()} ${r.url()}`);});
        page.on('requestfailed',r=>{if(r.url().split('?')[0].endsWith('.css'))failed.push(r.url());});
        try {
          const response=await page.goto(BASE+route,{waitUntil:'load',timeout:30000});
          assert.equal(response?.status(),200,`${route} ${width}px: HTTP incorrecto`);
          assert.deepEqual(failed,[],`${route} ${width}px: CSS no entregado`);
          const result=await page.evaluate(()=>{
            const root=getComputedStyle(document.documentElement);
            const main=document.querySelector('main#contenido');
            const r=main?.getBoundingClientRect();
            return {gutter:root.getPropertyValue('--page-gutter').trim(),gap:root.getPropertyValue('--grid-gap').trim(),gutterPx:parseFloat(root.getPropertyValue('--page-gutter')),mainWidth:r?.width,mainLeft:r?.left,mainRight:r?.right,overflow:document.documentElement.scrollWidth-document.documentElement.clientWidth};
          });
          assert.ok(result.gutter && result.gap,`${route} ${width}px: tokens CSS ausentes`);
          assert.ok(result.gutterPx>0,`${route} ${width}px: gutter no positivo (${result.gutter})`);
          assert.ok(result.mainWidth>0,`${route} ${width}px: contenido principal vacío`);
          assert.ok(result.mainLeft>=-1 && result.mainRight<=width+1,`${route} ${width}px: main fuera del viewport (${result.mainLeft}, ${result.mainRight})`);
          assert.ok(result.overflow<=1,`${route} ${width}px: overflow ${result.overflow}px`);
        }catch(e){failures.push(e.message);}finally{await page.close();}
      }));
    }finally{await context.close();}
  }
  assert.deepEqual(failures,[],failures.join('\n'));
  console.log('PASS editoriales concurrent CSS gutters');
}finally{await browser.close();}
