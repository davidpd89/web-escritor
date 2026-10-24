import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true});
try {
  for(const width of [320,390,768,1280]) {
    const context=await browser.newContext({viewport:{width,height:900}});
    const page=await context.newPage();
    try {
      await page.goto(`${BASE}/metodologia-editorial/`,{waitUntil:'load'});
      const checks=await page.evaluate(()=>{
        const parse=v=>(v.match(/[\d.]+/g)||[]).slice(0,3).map(Number);
        const luminance=v=>{
          const components=parse(v).map(x=>{x/=255;return x<=.04045?x/12.92:((x+.055)/1.055)**2.4;});
          return .2126*components[0]+.7152*components[1]+.0722*components[2];
        };
        const background=el=>{
          for(let n=el;n;n=n.parentElement){const color=getComputedStyle(n).backgroundColor;if(color&&!color.includes('0, 0, 0, 0')&&color!=='transparent')return color;}
          return 'rgb(255,255,255)';
        };
        const elements=[...document.querySelectorAll('.tool-findings-block>p,.spec-ledger dt,.spec-ledger dd,.tool-findings-block a,.tool-note')];
        return elements.map(el=>{
          const fg=luminance(getComputedStyle(el).color),bg=luminance(background(el));
          return {selector:el.tagName,text:(el.textContent||'').slice(0,45),ratio:(Math.max(fg,bg)+.05)/(Math.min(fg,bg)+.05)};
        });
      });
      assert.ok(checks.length>=15);
      for(const item of checks)assert.ok(item.ratio>=4.5,`${width}px: contraste ${item.ratio.toFixed(2)} en ${item.selector}: ${item.text}`);
    } finally {await context.close();}
  }
  console.log('PASS methodology effective contrast');
} finally {await browser.close();}