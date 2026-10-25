import assert from 'node:assert/strict';
import {chromium} from 'playwright';
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
const page=await browser.newPage({reducedMotion:'reduce'});
const origin=process.env.QA_ORIGIN||'http://127.0.0.1:8000';
try{
  await page.goto(origin+'/',{waitUntil:'load'});
  await page.evaluate(()=>{try{sessionStorage.setItem('dp-intro-seen','1')}catch{}});
  await page.reload({waitUntil:'load'});
  await page.evaluate(()=>document.fonts.ready);
  const buy=page.locator('.site-header .header-buy:visible').first();
  await buy.waitFor({state:'visible'});
  const href=await buy.getAttribute('href');
  assert.ok(href&&href.trim(),'Portada: el botón de compra no tiene destino');
  for(const state of ['normal','hover','focus']){
    if(state==='hover')await buy.hover();
    if(state==='focus')await buy.focus();
    const result=await buy.evaluate(el=>{
      const parse=s=>{const m=s.match(/rgba?\(([^)]+)\)/);if(!m)throw Error('Color no RGB '+s);return m[1].split(/[,\s/]+/).filter(Boolean).slice(0,3).map(Number)};
      const lum=c=>c.map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);
      const css=getComputedStyle(el);
      const a=lum(parse(css.color)),b=lum(parse(css.backgroundColor));
      return {ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05),foreground:css.color,background:css.backgroundColor};
    });
    assert.ok(result.ratio>=4.5,`Portada, botón de compra, ${state}: ${result.ratio.toFixed(2)}:1; texto ${result.foreground}; fondo ${result.background}`);
  }
}finally{await browser.close();}