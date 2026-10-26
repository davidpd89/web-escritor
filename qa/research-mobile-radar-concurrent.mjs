import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=(process.env.SITE_BASE_URL||'http://127.0.0.1:8000').replace(/\/$/,'');
const browser=await chromium.launch({headless:true});
try {
  await Promise.all(Array.from({length:12},async(_,i)=>{
    const width=[320,375,390][i%3];
    const context=await browser.newContext({viewport:{width,height:740},reducedMotion:'reduce',serviceWorkers:'block'});
    const page=await context.newPage();
    const errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    await page.route('**/*',r=>new URL(r.request().url()).origin===new URL(BASE).origin?r.continue():r.abort());
    try {
      const response=await page.goto(BASE+'/convocatorias-escritores/',{waitUntil:'load',timeout:30000});
      assert.equal(response?.status(),200,`/convocatorias-escritores/ ${width}px visita ${i}: HTTP ${response?.status()}`);
      const state=await page.evaluate(()=>{
        const main=document.querySelector('main');
        const r=main?.getBoundingClientRect();
        const controls=[...document.querySelectorAll('main input,main select,main button')].filter(el=>{
          const b=el.getBoundingClientRect(),s=getComputedStyle(el);
          return b.width>0&&b.height>0&&s.display!=='none'&&s.visibility!=='hidden';
        });
        return {text:main?.innerText.trim().length||0,visible:!!r&&r.width>0&&r.height>0,controls:controls.length,overflow:document.documentElement.scrollWidth-document.documentElement.clientWidth};
      });
      assert.ok(state.visible&&state.text>100,`/convocatorias-escritores/ ${width}px visita ${i}: documento principal vacío o invisible`);
      assert.ok(state.controls>0,`/convocatorias-escritores/ ${width}px visita ${i}: controles no disponibles`);
      assert.ok(state.overflow<=1,`/convocatorias-escritores/ ${width}px visita ${i}: desbordamiento ${state.overflow}px`);
      assert.deepEqual(errors,[],`/convocatorias-escritores/ ${width}px visita ${i}: ${errors.join('; ')}`);
    } finally {await context.close();}
  }));
  console.log('PASS radar concurrent mobile');
} finally {await browser.close();}
