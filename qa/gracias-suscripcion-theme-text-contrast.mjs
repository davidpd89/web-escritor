import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const ORIGIN=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true});
try{
  for(const scheme of ['light','dark']){
    const page=await browser.newPage({colorScheme:scheme,viewport:{width:390,height:844}});
    await page.goto(`${ORIGIN}/gracias-suscripcion/`,{waitUntil:'load'});
    const samples=await page.locator('main h1,main h2,main p,main .book-breadcrumb li').evaluateAll(nodes=>{
      const parse=s=>{const m=s.match(/rgba?\(([^)]+)\)/);if(!m)return null;const p=m[1].split(/[\s,\/]+/).filter(Boolean).map(Number);return [...p.slice(0,3),p[3]??1];};
      const blend=(f,b)=>f.slice(0,3).map((v,i)=>v*f[3]+b[i]*(1-f[3]));
      const lum=c=>c.map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4;}).reduce((a,v,i)=>a+v*[.2126,.7152,.0722][i],0);
      return nodes.filter(n=>n.getClientRects().length&&n.textContent.trim()).map(n=>{
        let ancestors=[];for(let e=n;e;e=e.parentElement)ancestors.unshift(e);
        let bg=[255,255,255];for(const e of ancestors){const c=parse(getComputedStyle(e).backgroundColor);if(c)bg=blend(c,bg);}
        const fg=parse(getComputedStyle(n).color);const a=lum(blend(fg,bg)),b=lum(bg);
        return {text:n.textContent.trim().slice(0,65),ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05),foreground:getComputedStyle(n).color,background:bg};
      });
    });
    assert(samples.length>=5,`/gracias-suscripcion/ ${scheme}: faltan muestras de texto`);
    for(const sample of samples)assert(sample.ratio>=4.5,`/gracias-suscripcion/ ${scheme}: ${sample.text}, contraste ${sample.ratio.toFixed(2)}:1, ${JSON.stringify(sample)}`);
    await page.close();
  }
}finally{await browser.close();}
console.log('gracias-suscripcion theme text contrast: PASS');