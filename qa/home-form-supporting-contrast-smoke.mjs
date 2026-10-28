import assert from 'node:assert/strict';
import {chromium} from 'playwright';
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
const page=await browser.newPage();
const origin=process.env.QA_ORIGIN||'http://127.0.0.1:8000';
try{
  await page.goto(origin+'/',{waitUntil:'load'});
  await page.evaluate(()=>{try{sessionStorage.setItem('dp-intro-seen','1')}catch{}});
  await page.reload({waitUntil:'load'});
  await page.locator('html[data-home-editorial-v3="true"]').waitFor();
  await page.evaluate(()=>document.fonts.ready);
  const result=await page.evaluate(()=>{
    const parse=s=>{const m=s.match(/rgba?\(([^)]+)\)/);if(!m)throw Error('Color no RGB '+s);const n=m[1].split(/[,\s/]+/).filter(Boolean).map(Number);return [...n.slice(0,3),n[3]??1]};
    const blend=(a,b)=>a.slice(0,3).map((v,i)=>v*a[3]+b[i]*(1-a[3]));
    const lum=c=>c.map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);
    const selectors='.form-help,.form-consent,.form-status,.yale-signup__consent-note';
    return [...document.querySelectorAll(selectors)].filter(el=>{const s=getComputedStyle(el);return el.getClientRects().length&&s.visibility==='visible'&&s.display!=='none'&&el.textContent.trim()}).map(el=>{
      let bg=[255,255,255];const chain=[];for(let p=el;p;p=p.parentElement)chain.unshift(p);
      for(const p of chain)bg=blend(parse(getComputedStyle(p).backgroundColor),bg);
      const fg=blend(parse(getComputedStyle(el).color),bg);
      const a=lum(fg),b=lum(bg);
      return {text:el.textContent.trim().slice(0,70),ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05),selector:el.className};
    });
  });
  assert.ok(result.length>0,'Portada: no se encontró texto visible de ayuda, consentimiento o estado');
  for(const item of result)assert.ok(item.ratio>=4.5,`Portada, ${item.selector}, texto ${item.text}: contraste ${item.ratio.toFixed(2)}:1; mínimo 4.5:1`);
}finally{await browser.close();}