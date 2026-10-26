import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=(process.env.QA_ORIGIN||process.env.SITE_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch({headless:true});
const routes=['/libros/','/libros/samuel-entre-mundos/'];
try {
  for(const route of routes)for(const scheme of ['light','dark']) {
    const page=await browser.newPage({viewport:{width:390,height:844},colorScheme:scheme,reducedMotion:'reduce'});
    const response=await page.goto(BASE+route,{waitUntil:'domcontentloaded'});
    assert.equal(response?.status(),200,`${route} ${scheme}: HTTP incorrecto`);
    await page.evaluate(()=>document.fonts.ready);
    const result=await page.evaluate(()=>{
      const rgb=s=>{const m=s.match(/^rgba?\(([^)]+)\)$/);return m?m[1].split(/[,\s/]+/).filter(Boolean).map(Number):null;};
      const mix=(a,b)=>a.slice(0,3).map((v,i)=>v*(a[3]??1)+b[i]*(1-(a[3]??1)));
      const lum=c=>c.map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4;}).reduce((n,v,i)=>n+v*[.2126,.7152,.0722][i],0);
      const elements=[...document.querySelectorAll('main p,main li,main dd')].filter(e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.width>0&&r.height>0&&s.visibility==='visible'&&e.textContent.trim()&&parseFloat(s.fontSize)>=12;});
      return elements.map(el=>{const s=getComputedStyle(el),chain=[];for(let n=el;n;n=n.parentElement)chain.unshift(n);let bg=[255,255,255];for(const n of chain){const c=rgb(getComputedStyle(n).backgroundColor);if(c)bg=mix(c,bg);}const fg=rgb(s.color);if(!fg)return {text:el.textContent.trim().slice(0,50),ratio:0};const a=lum(mix(fg,bg)),b=lum(bg);return {text:el.textContent.trim().slice(0,50),ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05)};});
    });
    assert.ok(result.length>0,`${route} ${scheme}: ningún texto visible analizado`);
    for(const item of result)assert.ok(item.ratio>=4.49,`${route} ${scheme}: texto ${JSON.stringify(item.text)} con contraste ${item.ratio.toFixed(2)}:1`);
    await page.close();
  }
} finally {await browser.close();}
console.log('PASS media-color-scheme-contrast');