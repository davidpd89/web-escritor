import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true});
const viewports=[{width:320,height:640},{width:390,height:844},{width:667,height:375},{width:768,height:1024},{width:1280,height:800}];
const selectors=['main .book-breadcrumb a[href="/editoriales/"]','main .tool-findings-block a[data-email-reveal]','.section-context a[aria-current="page"]'];
try {
  for(const viewport of viewports) {
    const context=await browser.newContext({viewport,reducedMotion:'reduce'});
    const page=await context.newPage();
    try {
      await page.goto(`${BASE}/metodologia-editorial/`,{waitUntil:'load'});
      for(const selector of selectors) {
        const locator=page.locator(selector).first();
        assert.equal(await locator.count(),1,selector);
        await locator.scrollIntoViewIfNeeded();
        const hit=await locator.evaluate(el=>{
          const r=el.getBoundingClientRect();
          const x=r.left+r.width/2,y=r.top+r.height/2;
          const target=document.elementFromPoint(x,y);
          return {width:r.width,height:r.height,x,y,inside:x>=0&&y>=0&&x<innerWidth&&y<innerHeight,correct:target===el||el.contains(target),tag:target?.tagName||null};
        });
        assert.ok(hit.width>0&&hit.height>0,`${selector}: sin superficie`);
        assert.equal(hit.inside,true,`${selector}: centro fuera del viewport`);
        assert.equal(hit.correct,true,`${selector}: interceptado por ${hit.tag} en ${viewport.width}x${viewport.height}`);
      }
    } finally { await context.close(); }
  }
  console.log('PASS methodology geometric hit testing');
} finally { await browser.close(); }