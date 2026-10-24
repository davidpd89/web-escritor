import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const routes=[
  ['/convocatorias-escritores/','[data-radar-item]:visible [data-radar-source]'],
  ['/editoriales/','[data-editorial-card]:visible a[href]'],
  ['/recursos/herramientas-para-escritores/','.wt-card:visible a[href]'],
  ['/cuaderno/temas/fantasia-de-portales/','.cuaderno-topic-step a[href]'],
  ['/recomendaciones/','[data-catalogue-book]:visible a[href]']
];
const browser=await chromium.launch({headless:true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});
try {
  for(const width of [320,390]){
    const context=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});
    for(const [route,selector] of routes){
      const page=await context.newPage();
      assert.equal((await page.goto(ORIGIN+route,{waitUntil:'networkidle'})).status(),200);
      const links=page.locator(selector);
      const count=Math.min(await links.count(),5);
      assert.ok(count>0,`${route}: faltan acciones`);
      for(let i=0;i<count;i++){
        const link=links.nth(i);
        await link.scrollIntoViewIfNeeded();
        const result=await link.evaluate(el=>{
          const r=el.getBoundingClientRect();
          const x=Math.max(0,Math.min(innerWidth-1,r.left+r.width/2));
          const y=Math.max(0,Math.min(innerHeight-1,r.top+r.height/2));
          const hit=document.elementFromPoint(x,y);
          const font=parseFloat(getComputedStyle(el).fontSize);
          return {width:r.width,height:r.height,font,hit:!!hit&&(el===hit||el.contains(hit)),name:(el.getAttribute('aria-label')||el.innerText||el.textContent||'').trim()};
        });
        assert.ok(result.width>0&&result.height>0,`${route}: CTA sin geometría`);
        assert.ok(result.font>=12,`${route}: acción con texto demasiado pequeño`);
        assert.ok(result.name,`${route}: enlace sin nombre accesible`);
        assert.ok(result.hit,`${route}: acción interceptada`);
      }
      await page.close();
    }
    await context.close();
  }
} finally {
  await browser.close();
}
console.log('OK: acciones editoriales comprobadas en cinco familias y dos anchuras');
