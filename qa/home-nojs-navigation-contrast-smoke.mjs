import assert from 'node:assert/strict';
import {chromium} from 'playwright';
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
const context=await browser.newContext({javaScriptEnabled:false,reducedMotion:'reduce'});
const page=await context.newPage();
const origin=process.env.QA_ORIGIN||'http://127.0.0.1:8000';
try{
  const response=await page.goto(origin+'/',{waitUntil:'load'});
  assert.equal(response.status(),200,'Portada sin JS: HTTP incorrecto');
  const links=page.locator('.primary-nav a:visible');
  const count=await links.count();
  assert.ok(count>0,'Portada sin JS: navegación alternativa ausente');
  for(let i=0;i<count;i++){
    const link=links.nth(i);
    const name=(await link.innerText()).trim();
    assert.ok(await link.getAttribute('href'),`Portada sin JS: ${name} carece de destino`);
    for(const state of ['normal','focus']){
      if(state==='focus')await link.focus();
      const result=await link.evaluate(el=>{
        const parse=s=>{const m=s.match(/rgba?\(([^)]+)\)/);if(!m)throw Error('Color no RGB '+s);const n=m[1].split(/[,\s/]+/).filter(Boolean).map(Number);return [...n.slice(0,3),n[3]??1]};
        const blend=(a,b)=>a.slice(0,3).map((v,i)=>v*a[3]+b[i]*(1-a[3]));
        let bg=[255,255,255],chain=[];for(let p=el;p;p=p.parentElement)chain.unshift(p);
        for(const p of chain)bg=blend(parse(getComputedStyle(p).backgroundColor),bg);
        const fg=blend(parse(getComputedStyle(el).color),bg);
        const lum=c=>c.map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);
        const a=lum(fg),b=lum(bg);
        return {ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05),visibility:getComputedStyle(el).visibility};
      });
      assert.equal(result.visibility,'visible',`Portada sin JS, ${name}, ${state}: enlace oculto`);
      assert.ok(result.ratio>=4.5,`Portada sin JS, ${name}, ${state}: contraste ${result.ratio.toFixed(2)}:1; mínimo 4.5:1`);
    }
  }
}finally{await context.close();await browser.close();}