import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const O=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true});
try {
  const context=await browser.newContext({serviceWorkers:'block'});
  await context.route('**/*',r=>r.request().url().startsWith(O+'/')?r.continue():r.abort());
  const page=await context.newPage();
  await page.goto(O+'/empieza-aqui/');
  const cases=[['.findability-hero__kicker',4.5],['.findability-hero h1',3],['.findability-entry h2',3],['.findability-links a',4.5]];
  for(const [selector,min] of cases) {
    const ratio=await page.locator(selector).first().evaluate(el=>{
      const rgb=s=>(s.match(/[\d.]+/g)||[]).slice(0,3).map(Number);
      const lum=v=>{
        const x=v.map(n=>n/255).map(n=>n<=0.04045?n/12.92:((n+0.055)/1.055)**2.4);
        return 0.2126*x[0]+0.7152*x[1]+0.0722*x[2];
      };
      const fg=rgb(getComputedStyle(el).color);
      let node=el,bg=[255,255,255];
      while(node) {
        const color=getComputedStyle(node).backgroundColor;
        if(color&&color!=='transparent'&&!/^rgba\([^)]*,\s*0\s*\)$/.test(color)) {bg=rgb(color);break;}
        node=node.parentElement;
      }
      const a=lum(fg),b=lum(bg);
      return (Math.max(a,b)+0.05)/(Math.min(a,b)+0.05);
    });
    assert(ratio>=min,`${selector}: contraste ${ratio.toFixed(2)}:1 inferior a ${min}:1`);
  }
  await context.close();
} finally {await browser.close();}
console.log('EMPIEZA CONTRAST: OK');