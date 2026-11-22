import assert from 'node:assert/strict';
import {chromium} from 'playwright';

// Secuencias aleatorias (con semilla) de acciones de usuario sobre el catálogo: marcar/desmarcar facetas, paginar,
// saltar a una página, Atrás, Adelante y recargar. Tras cada acción: hash, casillas, página mostrada y fichas
// visibles deben decir lo mismo, sin páginas fuera de rango ni errores de consola (ChatGPT + David, 22/11).
const BASE=(process.env.QA_ORIGIN||process.env.SITE_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const SEED=Number(process.env.FUZZ_SEED||20261122), RUNS=Number(process.env.FUZZ_RUNS||12), STEPS=Number(process.env.FUZZ_STEPS||14);
let s=SEED>>>0;
const rng=()=>{s=(s+0x6D2B79F5)>>>0;let t=s;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return((t^t>>>14)>>>0)/4294967296;};
const pick=xs=>xs[Math.floor(rng()*xs.length)];
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
const errors=[], trace=[];
const settle=page=>page.waitForFunction(()=>{const r=document.querySelector('[data-reading-catalogue]');return r?.dataset.catalogueReady&&!r.dataset.facetsPending;},null,{timeout:90000});
async function check(page,label){
  const st=await page.evaluate(()=>{
    const root=document.querySelector('[data-reading-catalogue]');
    const hash=new URLSearchParams(location.hash.slice(1));
    const boxes=[...root.querySelectorAll('input[data-facet]')].filter(b=>b.checked).map(b=>`${b.dataset.facet}=${b.value}`).sort();
    const fromHash=[...hash.entries()].filter(([k])=>['grupo','genero','edad','formato'].includes(k)).map(([k,v])=>`${k}=${v}`).sort();
    const cards=[...root.querySelectorAll('.catalogue-card')].filter(c=>!c.hidden&&c.offsetParent!==null).length;
    const text=root.querySelector('[data-catalogue-count]').textContent;
    const total=Number((text.match(/^([\d.]+)/)||[])[1]?.replace(/\./g,'')||0), pg=text.match(/página (\d+) de (\d+)/);
    return {boxes,fromHash,cards,total,page:pg?Number(pg[1]):1,pages:pg?Number(pg[2]):1,hashPage:Number(hash.get('pagina')||1),text};
  });
  const where=`${label} → ${JSON.stringify(st)}`;
  assert.deepEqual(st.boxes,st.fromHash,`casillas ≠ hash: ${where}`);
  assert.ok(st.page>=1&&st.page<=st.pages,`página fuera de rango: ${where}`);
  assert.equal(st.hashPage,st.page,`hash de página ≠ página mostrada: ${where}`);
  assert.ok(st.cards<=24,`más de 24 fichas: ${where}`);
  if(st.total>0)assert.ok(st.cards>0,`recuento ${st.total} pero 0 fichas: ${where}`);
}
try {
  for(let run=0;run<RUNS;run++){
    const ctx=await browser.newContext({viewport:{width:1440,height:1000}});
    const page=await ctx.newPage();
    await page.addInitScript(()=>{try{localStorage.setItem('nl-popup-ts',String(Date.now()));}catch{}});
    page.on('pageerror',e=>errors.push(e.message));
    await page.goto(BASE+'/recomendaciones/#',{waitUntil:'networkidle'});
    await page.locator('[data-catalogue-filters] summary').first().focus();
    await settle(page);
    trace.length=0;
    for(let i=0;i<STEPS;i++){
      const kind=pick(['facet','facet','next','prev','jump','back','forward','reload']);
      let label=kind;
      if(kind==='facet'){
        const boxes=await page.$$('[data-catalogue-filters] input[data-facet]');
        const live=[];for(const b of boxes){if(await b.evaluate(x=>!x.closest('label').hidden&&!x.disabled))live.push(b);}
        if(!live.length)continue;
        const b=pick(live); label=`facet ${await b.evaluate(x=>x.dataset.facet+'='+x.value)}`;
        await b.evaluate(x=>x.click());
      } else if(kind==='next'||kind==='prev'){
        const btn=page.locator('.catalogue-pagination button',{hasText:kind==='next'?'Siguiente':'Anterior'}).first();
        if(!await btn.count()||!await btn.isVisible()||await btn.isDisabled())continue; await btn.click();
      } else if(kind==='jump'){
        const nums=page.locator('.catalogue-pagination button[aria-label^="Página"]');
        const n=await nums.count(); if(!n)continue; const t=nums.nth(Math.floor(rng()*n)); label=`jump ${await t.getAttribute('aria-label')}`; if(!await t.isVisible()||await t.isDisabled())continue; await t.click();
      } else if(kind==='back'){await page.goBack({waitUntil:'commit'}).catch(()=>{});}
      else if(kind==='forward'){await page.goForward({waitUntil:'commit'}).catch(()=>{});}
      else {await page.reload({waitUntil:'networkidle'}); await page.locator('[data-catalogue-filters] summary').first().focus();}
      trace.push(label);
      if(!/\/recomendaciones\/(#.*)?$/.test(page.url())){trace.push('(salió del listado)');break;}
      await settle(page); await page.waitForTimeout(150);
      await check(page,`run ${run} paso ${i} [${trace.join(' > ')}]`);
    }
    await ctx.close();
  }
  assert.deepEqual(errors,[],'errores de página: '+errors.join(' | '));
  console.log(`PASS catalogue-sequence-fuzz (${RUNS} secuencias × ${STEPS} pasos, semilla ${SEED})`);
} finally { await browser.close(); }
