import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:8000';
const browser = await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
const context = await browser.newContext({reducedMotion:'reduce'});
const page = await context.newPage();

async function contrast(locator) {
  return locator.evaluate(el => {
    const rgb = s => {
      const m = s.match(/rgba?\(([^)]+)\)/);
      if (!m) throw Error('Color no RGB: '+s);
      const n = m[1].split(/[,\s/]+/).filter(Boolean).map(Number);
      return [...n.slice(0,3),n[3]??1];
    };
    const blend = (a,b) => a.slice(0,3).map((v,i)=>v*a[3]+b[i]*(1-a[3]));
    const luminance = c => c.slice(0,3).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);
    const style = getComputedStyle(el);
    let bg=[255,255,255];
    const ancestors=[];
    for(let p=el;p;p=p.parentElement) ancestors.unshift(p);
    for(const p of ancestors) bg=blend(rgb(getComputedStyle(p).backgroundColor),bg);
    const fg=blend(rgb(style.color),bg);
    const a=luminance(fg),b=luminance(bg);
    const ratio=(Math.max(a,b)+.05)/(Math.min(a,b)+.05);
    const size=parseFloat(style.fontSize),weight=parseInt(style.fontWeight)||400;
    return {ratio,minimum:size>=24||(size>=18.66&&weight>=700)?3:4.5,color:style.color,background:bg};
  });
}

try {
  const response=await page.goto(ORIGIN+'/',{waitUntil:'load'});
  assert.equal(response.status(),200,'Portada: respuesta HTTP');
  await page.evaluate(()=>{try{sessionStorage.setItem('dp-intro-seen','1')}catch{}});
  await page.reload({waitUntil:'load'});
  await page.locator('html[data-home-editorial-v3="true"]').waitFor();
  await page.evaluate(()=>document.fonts.ready);
  const actions=page.locator('main a.header-buy:visible, main button.form-submit:visible, main a.text-action:visible');
  const count=await actions.count();
  assert.ok(count>0,'Portada: no se encontraron acciones principales visibles');
  for(let i=0;i<Math.min(count,8);i++){
    const el=actions.nth(i);
    const name=(await el.innerText()).trim();
    for(const state of ['reposo','hover','foco']){
      if(state==='hover')await el.hover();
      if(state==='foco')await el.focus();
      await page.waitForFunction(()=>document.fonts.status==='loaded');
      const c=await contrast(el);
      assert.ok(c.ratio+.01>=c.minimum,`Portada, acción ${name}, ${state}: contraste ${c.ratio.toFixed(2)}:1; mínimo ${c.minimum}:1; color ${c.color}; fondo ${c.background}`);
    }
    await el.blur();
  }
} finally {await context.close();await browser.close();}