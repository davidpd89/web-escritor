import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=(process.env.QA_ORIGIN||process.env.SITE_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch({headless:true});
try {
  for(const width of [360,1280]) {
    const page=await browser.newPage({viewport:{width,height:900},reducedMotion:'reduce'});
    const response=await page.goto(BASE+'/libros/',{waitUntil:'domcontentloaded'});
    assert.equal(response?.status(),200,`/libros/ ${width}px: HTTP incorrecto`);
    const links=page.locator('.books-stage__copy a[href]');
    const count=await links.count();
    assert.ok(count>0,`/libros/ ${width}px: no se encontraron enlaces editoriales`);
    for(let i=0;i<count;i++) {
      const link=links.nth(i);
      if(!await link.isVisible())continue;
      await link.focus();
      const result=await link.evaluate(el=>{
        const rgb=s=>{const m=s.match(/^rgba?\(([^)]+)\)$/);return m?m[1].split(/[,\s/]+/).filter(Boolean).map(Number):null;};
        const mix=(a,b)=>a.slice(0,3).map((v,i)=>v*(a[3]??1)+b[i]*(1-(a[3]??1)));
        const lum=c=>c.map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4;}).reduce((n,v,i)=>n+v*[.2126,.7152,.0722][i],0);
        const s=getComputedStyle(el),chain=[];for(let n=el;n;n=n.parentElement)chain.unshift(n);let bg=[255,255,255];for(const n of chain){const c=rgb(getComputedStyle(n).backgroundColor);if(c)bg=mix(c,bg);}const outline=rgb(s.outlineColor);const fg=outline?mix(outline,bg):bg;const a=lum(fg),b=lum(bg);return {href:el.getAttribute('href'),focused:el.matches(':focus-visible'),style:s.outlineStyle,width:parseFloat(s.outlineWidth),ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05)};
      });
      assert.ok(result.focused,`/libros/ ${width}px: ${result.href} no muestra :focus-visible`);
      assert.ok(result.style!=='none'&&result.width>=2,`/libros/ ${width}px: ${result.href} sin contorno de foco suficiente`);
      assert.ok(result.ratio>=3,`/libros/ ${width}px: foco de ${result.href} con contraste ${result.ratio.toFixed(2)}:1`);
    }
    await page.close();
  }
} finally {await browser.close();}
console.log('PASS media-keyboard-focus-contrast');