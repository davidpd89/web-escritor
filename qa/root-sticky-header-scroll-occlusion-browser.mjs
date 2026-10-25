import assert from 'node:assert/strict';
import { chromium } from 'playwright';

assert.ok(process.env.QA_ORIGIN,'Se necesita QA_ORIGIN');
const browser=await chromium.launch({headless:true});
try {
  for(const width of [390,768,900,1280]) {
    const page=await browser.newPage({viewport:{width,height:720},reducedMotion:'reduce'});
    await page.addInitScript(()=>{try{sessionStorage.setItem('dp-intro-seen','true')}catch{}});
    await page.goto(new URL('/',process.env.QA_ORIGIN).href,{waitUntil:'load'});
    await page.evaluate(()=>document.fonts.ready);
    await page.evaluate(()=>scrollTo(0,Math.min(600,document.documentElement.scrollHeight-innerHeight)));
    await page.waitForFunction(()=>document.querySelector('[data-header]')?.dataset.scrolled==='true');
    const candidates=page.locator('main a[href]:visible, main button:visible');
    const count=Math.min(await candidates.count(),12);
    assert.ok(count>0,`Portada ${width}px: sin controles de contenido`);
    for(let i=0;i<count;i++) {
      const el=candidates.nth(i);
      await el.scrollIntoViewIfNeeded();
      const state=await el.evaluate(node=>{
        const r=node.getBoundingClientRect();
        const header=document.querySelector('.site-header');
        const h=header?.getBoundingClientRect();
        const overlap=h&&r.top<h.bottom&&r.bottom>h.top;
        const x=Math.min(innerWidth-1,Math.max(0,r.left+r.width/2));
        const y=Math.min(innerHeight-1,Math.max(0,r.top+r.height/2));
        const hit=document.elementFromPoint(x,y);
        return {overlap,hit:hit===node||node.contains(hit),rect:{top:r.top,bottom:r.bottom},headerBottom:h?.bottom};
      });
      assert.ok(!state.overlap||state.hit,`Portada ${width}px: control ${i} tapado por cabecera; ${JSON.stringify(state)}`);
    }
    await page.close();
  }
}finally{await browser.close();}