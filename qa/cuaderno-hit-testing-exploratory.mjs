import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const routes = ['/cuaderno/', '/cuaderno/temas/', '/cuaderno/temas/fantasia-de-portales/', '/cuaderno/que-es-el-portal-fantasy/'];
const browser = await chromium.launch({headless:true});
try {
  for (const width of [320,390,768]) {
    const context = await browser.newContext({viewport:{width,height:900}});
    await context.route(/^https?:\/\/(?!127\.0\.0\.1|localhost)/, r => r.abort());
    const page = await context.newPage();
    for (const route of routes) {
      const response = await page.goto(BASE + route);
      assert.equal(response.status(),200,route);
      await page.evaluate(() => {document.documentElement.style.fontSize='200%';});
      const links = page.locator('main a[href^="/"]');
      const count = await links.count();
      assert.ok(count>0,`${route}: ningún enlace`);
      for (let i=0;i<count;i++) {
        const link=links.nth(i);
        if (!await link.isVisible()) continue;
        await link.scrollIntoViewIfNeeded();
        const result=await link.evaluate(el=>{
          const r=el.getBoundingClientRect();
          const x=Math.max(0,Math.min(innerWidth-1,r.left+r.width/2));
          const y=Math.max(0,Math.min(innerHeight-1,r.top+r.height/2));
          const target=document.elementFromPoint(x,y);
          return {href:el.getAttribute('href'),width:r.width,height:r.height,hit:!!target&&(target===el||el.contains(target)||target.contains(el))};
        });
        assert.ok(result.width>0&&result.height>0,`${route}: enlace sin superficie ${result.href}`);
        assert.ok(result.hit,`${route}: enlace obstruido ${result.href}`);
      }
    }
    await context.close();
  }
  console.log('PASS cuaderno hit testing');
} finally {await browser.close();}
