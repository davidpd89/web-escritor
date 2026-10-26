import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=(process.env.QA_ORIGIN||process.env.SITE_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch({headless:true});
try {
  for(const width of [360,768,1280]) {
    const page=await browser.newPage({viewport:{width,height:900},reducedMotion:'reduce'});
    const response=await page.goto(BASE+'/libros/',{waitUntil:'domcontentloaded'});
    assert.equal(response?.status(),200,`/libros/ ${width}px: HTTP incorrecto`);
    await page.evaluate(()=>document.fonts.ready);
    const results=await page.locator('.books-stage__copy').evaluateAll(nodes=>{
      const parse=s=>{const m=s.match(/^rgba?\(([^)]+)\)$/);if(!m)return null;const a=m[1].split(/[,\s/]+/).filter(Boolean).map(Number);return a.length>=3?[...a.slice(0,3),a[3]??1]:null;};
      const composite=(fg,bg)=>fg.slice(0,3).map((v,i)=>v*fg[3]+bg[i]*(1-fg[3]));
      const surface=el=>{let bg=[255,255,255];const chain=[];for(let n=el;n;n=n.parentElement)chain.unshift(n);for(const n of chain){const c=parse(getComputedStyle(n).backgroundColor);if(c)bg=composite(c,bg);}return bg;};
      const luminance=rgb=>rgb.map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4;}).reduce((a,v,i)=>a+v*[.2126,.7152,.0722][i],0);
      const ratio=(a,b)=>{const x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);};
      return nodes.flatMap(node=>[...node.querySelectorAll('h2,p,dt,dd')].filter(el=>{const r=el.getBoundingClientRect(),s=getComputedStyle(el);return r.width>0&&r.height>0&&s.visibility==='visible'&&s.display!=='none'&&el.textContent.trim();}).map(el=>{const s=getComputedStyle(el),bg=surface(el),fg=parse(s.color),size=parseFloat(s.fontSize),bold=parseInt(s.fontWeight,10)>=700;return {text:el.textContent.trim().slice(0,70),ratio:fg?ratio(composite(fg,bg),bg):0,minimum:size>=24||(size>=18.66&&bold)?3:4.5};}));
    });
    assert.ok(results.length>0,`/libros/ ${width}px: ningún texto editorial analizado`);
    for(const item of results)assert.ok(item.ratio+.01>=item.minimum,`/libros/ ${width}px: contraste ${item.ratio.toFixed(2)}:1, mínimo ${item.minimum}:1 en ${JSON.stringify(item.text)}`);
    await page.close();
  }
} finally {await browser.close();}
console.log('PASS media-adjacent-text-contrast');