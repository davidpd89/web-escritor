import assert from 'node:assert/strict';
import fs from 'node:fs';
import {chromium} from 'playwright';

const BASE=process.env.QA_ORIGIN||process.env.QA_BASE_URL||'http://127.0.0.1:4173';
const expected=JSON.parse(fs.readFileSync('editoriales/editoriales-data.json','utf8')).publishers.length;
assert.ok(expected>0,'editoriales: dataset público vacío');
const widths=[320,768,1024,1440];
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
const failures=[];
try {
  await Promise.all(widths.flatMap(width=>Array.from({length:3},(_,visit)=>({width,visit}))).map(async ({width,visit})=>{
    const context=await browser.newContext({viewport:{width,height:900}});
    const page=await context.newPage();
    try {
      const response=await page.goto(BASE+'/editoriales/',{waitUntil:'load',timeout:30000});
      assert.equal(response?.status(),200,`/editoriales/ ${width}px visita ${visit}: HTTP incorrecto`);
      const cards=page.locator('[data-editorial-card]');
      assert.equal(await cards.count(),expected,`/editoriales/ ${width}px visita ${visit}: número de tarjetas incorrecto`);
      const result=await cards.evaluateAll(nodes=>nodes.map((el,i)=>{
        const r=el.getBoundingClientRect();
        const links=[...el.querySelectorAll('a[href]')].filter(a=>{const u=new URL(a.href,location.href);return u.origin===location.origin && u.pathname.startsWith('/editoriales/') && u.pathname!=='/editoriales/';});
        return {i,left:r.left,right:r.right,width:r.width,links:links.length,title:el.querySelector('h2')?.textContent.trim()};
      }));
      for(const card of result){
        assert.ok(card.title,`/editoriales/ ${width}px visita ${visit}: tarjeta ${card.i} sin título`);
        assert.ok(card.links>0,`/editoriales/ ${width}px visita ${visit}: tarjeta ${card.i} sin enlace de detalle`);
        assert.ok(card.width>0 && card.left>=-1 && card.right<=width+1,`/editoriales/ ${width}px visita ${visit}: tarjeta ${card.i} desbordada (${card.left},${card.right})`);
      }
      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-document.documentElement.clientWidth);
      assert.ok(overflow<=1,`/editoriales/ ${width}px visita ${visit}: overflow ${overflow}px`);
    }catch(e){failures.push(e.message);}finally{await context.close();}
  }));
  assert.deepEqual(failures,[],failures.join('\n'));
  console.log('PASS editoriales concurrent card containment');
}finally{await browser.close();}
